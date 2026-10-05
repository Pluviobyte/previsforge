"""Deterministic, Blender-independent validation for SceneSpec documents."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable

from .model import EntitySpec, Keyframe, SceneSpec


SUPPORTED_VERSIONS = {"1.0"}
SUPPORTED_KINDS = {"box", "sphere", "cylinder", "torus", "plane", "actor", "empty"}


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    path: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {
            "severity": self.severity,
            "code": self.code,
            "path": self.path,
            "message": self.message,
        }


@dataclass(frozen=True)
class ValidationReport:
    findings: tuple[Finding, ...]

    @property
    def errors(self) -> tuple[Finding, ...]:
        return tuple(item for item in self.findings if item.severity == "error")

    @property
    def warnings(self) -> tuple[Finding, ...]:
        return tuple(item for item in self.findings if item.severity == "warning")

    @property
    def valid(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict[str, object]:
        return {
            "valid": self.valid,
            "summary": {"errors": len(self.errors), "warnings": len(self.warnings)},
            "findings": [finding.to_dict() for finding in self.findings],
        }


def _track_findings(
    keyframes: Iterable[Keyframe], duration: float, path: str
) -> list[Finding]:
    frames = tuple(keyframes)
    findings: list[Finding] = []
    times = [item.time for item in frames]
    if times != sorted(times) or len(times) != len(set(times)):
        findings.append(
            Finding(
                "error",
                "keyframes_not_monotonic",
                path,
                "Keyframe times must be strictly increasing.",
            )
        )
    if any(time < 0 or time > duration for time in times):
        findings.append(
            Finding(
                "error",
                "keyframe_out_of_range",
                path,
                f"Keyframes must stay inside 0..{duration:g} seconds.",
            )
        )
    return findings


def _entity_findings(entity: EntitySpec, index: int, duration: float) -> list[Finding]:
    path = f"entities[{index}]"
    findings = _track_findings(entity.keyframes, duration, f"{path}.keyframes")
    if not entity.id.strip():
        findings.append(Finding("error", "empty_id", f"{path}.id", "Entity ID cannot be empty."))
    if entity.kind not in SUPPORTED_KINDS:
        findings.append(
            Finding("error", "unsupported_kind", f"{path}.kind", f"Unsupported kind: {entity.kind}")
        )
    if any(not math.isfinite(value) or value <= 0 for value in entity.dimensions):
        findings.append(
            Finding(
                "error",
                "invalid_dimensions",
                f"{path}.dimensions",
                "All dimensions must be greater than zero.",
            )
        )
    if any(value < 0 or value > 1 for value in entity.color):
        findings.append(
            Finding("error", "invalid_color", f"{path}.color", "Color channels must be in 0..1.")
        )
    return findings


def _aabb(entity: EntitySpec) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    half = tuple(abs(entity.dimensions[index] * entity.scale[index]) / 2 for index in range(3))
    return (
        tuple(entity.location[index] - half[index] for index in range(3)),
        tuple(entity.location[index] + half[index] for index in range(3)),
    )


def _aabb_overlaps(
    left: tuple[tuple[float, float, float], tuple[float, float, float]],
    right: tuple[tuple[float, float, float], tuple[float, float, float]],
) -> bool:
    return all(left[0][axis] < right[1][axis] and right[0][axis] < left[1][axis] for axis in range(3))


def _segment_intersects_aabb(
    start: tuple[float, float, float],
    end: tuple[float, float, float],
    bounds: tuple[tuple[float, float, float], tuple[float, float, float]],
) -> bool:
    lower, upper = bounds
    t_min, t_max = 0.0, 1.0
    for axis in range(3):
        delta = end[axis] - start[axis]
        if abs(delta) < 1e-9:
            if start[axis] < lower[axis] or start[axis] > upper[axis]:
                return False
            continue
        near = (lower[axis] - start[axis]) / delta
        far = (upper[axis] - start[axis]) / delta
        if near > far:
            near, far = far, near
        t_min = max(t_min, near)
        t_max = min(t_max, far)
        if t_min > t_max:
            return False
    return True


def _spatial_findings(scene: SceneSpec) -> list[Finding]:
    findings: list[Finding] = []
    colliders = [
        entity
        for entity in scene.entities
        if entity.metadata.get("collision", True) is not False and not entity.keyframes
    ]
    for left_index, left in enumerate(colliders):
        for right in colliders[left_index + 1 :]:
            if _aabb_overlaps(_aabb(left), _aabb(right)):
                findings.append(
                    Finding(
                        "warning",
                        "static_overlap",
                        f"entities.{left.id}",
                        f"Static collision bounds overlap '{right.id}'.",
                    )
                )

    camera_points = [scene.camera.location]
    camera_points.extend(
        keyframe.location for keyframe in scene.camera.keyframes if keyframe.location is not None
    )
    blockers = [
        entity
        for entity in scene.entities
        if entity.metadata.get("camera_blocker", entity.metadata.get("collision", True)) is not False
        and not entity.keyframes
    ]
    warned: set[str] = set()
    for start, end in zip(camera_points, camera_points[1:]):
        if start == end:
            continue
        for blocker in blockers:
            if blocker.id not in warned and _segment_intersects_aabb(start, end, _aabb(blocker)):
                warned.add(blocker.id)
                findings.append(
                    Finding(
                        "warning",
                        "camera_path_obstructed",
                        "camera.keyframes",
                        f"Camera path crosses the approximate bounds of '{blocker.id}'.",
                    )
                )
    return findings


def validate_scene(scene: SceneSpec) -> ValidationReport:
    findings: list[Finding] = []
    if scene.version not in SUPPORTED_VERSIONS:
        findings.append(
            Finding("error", "unsupported_version", "version", f"Unsupported version: {scene.version}")
        )
    if scene.duration_seconds <= 0:
        findings.append(
            Finding("error", "invalid_duration", "duration_seconds", "Duration must be positive.")
        )
    if scene.fps <= 0:
        findings.append(Finding("error", "invalid_fps", "fps", "FPS must be positive."))
    if any(value <= 0 for value in scene.resolution):
        findings.append(
            Finding("error", "invalid_resolution", "resolution", "Resolution must be positive.")
        )

    seen: set[str] = set()
    for index, entity in enumerate(scene.entities):
        if entity.id in seen:
            findings.append(
                Finding(
                    "error",
                    "duplicate_id",
                    f"entities[{index}].id",
                    f"Entity ID '{entity.id}' is duplicated.",
                )
            )
        seen.add(entity.id)
        findings.extend(_entity_findings(entity, index, scene.duration_seconds))

    if scene.camera.id in seen:
        findings.append(
            Finding("error", "duplicate_id", "camera.id", "Camera ID duplicates an entity ID.")
        )
    if scene.camera.target is not None and scene.camera.target not in seen:
        findings.append(
            Finding(
                "error",
                "missing_camera_target",
                "camera.target",
                f"Camera target '{scene.camera.target}' does not exist.",
            )
        )
    if scene.camera.focal_length <= 0:
        findings.append(
            Finding("error", "invalid_focal_length", "camera.focal_length", "Focal length must be positive.")
        )
    findings.extend(
        _track_findings(scene.camera.keyframes, scene.duration_seconds, "camera.keyframes")
    )
    for index, marker in enumerate(scene.markers):
        if marker.time < 0 or marker.time > scene.duration_seconds:
            findings.append(
                Finding(
                    "error",
                    "marker_out_of_range",
                    f"markers[{index}].time",
                    "Marker falls outside the scene duration.",
                )
            )
    findings.extend(_spatial_findings(scene))
    return ValidationReport(tuple(findings))
