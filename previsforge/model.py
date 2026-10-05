"""Versioned domain model for portable previsualization scenes."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any, Iterable


JsonObject = dict[str, Any]
Vec3 = tuple[float, float, float]
Color = tuple[float, float, float, float]


class SceneSpecError(ValueError):
    """Raised when a SceneSpec cannot be decoded."""


def _numbers(value: Any, length: int, field_name: str) -> tuple[float, ...]:
    if not isinstance(value, (list, tuple)) or len(value) != length:
        raise SceneSpecError(f"{field_name} must contain {length} numbers")
    if any(not isinstance(item, (int, float)) or isinstance(item, bool) for item in value):
        raise SceneSpecError(f"{field_name} must contain only numbers")
    return tuple(float(item) for item in value)


def _vec3(value: Any, field_name: str) -> Vec3:
    return _numbers(value, 3, field_name)  # type: ignore[return-value]


def _color(value: Any, field_name: str) -> Color:
    return _numbers(value, 4, field_name)  # type: ignore[return-value]


@dataclass(frozen=True)
class Keyframe:
    time: float
    location: Vec3 | None = None
    rotation: Vec3 | None = None
    scale: Vec3 | None = None
    focal_length: float | None = None

    @classmethod
    def from_dict(cls, data: JsonObject, path: str) -> "Keyframe":
        try:
            time = float(data["time"])
        except (KeyError, TypeError, ValueError) as error:
            raise SceneSpecError(f"{path}.time must be a number") from error
        return cls(
            time=time,
            location=_vec3(data["location"], f"{path}.location") if "location" in data else None,
            rotation=_vec3(data["rotation"], f"{path}.rotation") if "rotation" in data else None,
            scale=_vec3(data["scale"], f"{path}.scale") if "scale" in data else None,
            focal_length=float(data["focal_length"]) if "focal_length" in data else None,
        )

    def to_dict(self) -> JsonObject:
        result: JsonObject = {"time": self.time}
        for name in ("location", "rotation", "scale"):
            value = getattr(self, name)
            if value is not None:
                result[name] = list(value)
        if self.focal_length is not None:
            result["focal_length"] = self.focal_length
        return result


@dataclass(frozen=True)
class EntitySpec:
    id: str
    name: str
    kind: str
    dimensions: Vec3
    color: Color = (0.72, 0.74, 0.78, 1.0)
    location: Vec3 = (0.0, 0.0, 0.0)
    rotation: Vec3 = (0.0, 0.0, 0.0)
    scale: Vec3 = (1.0, 1.0, 1.0)
    keyframes: tuple[Keyframe, ...] = ()
    metadata: JsonObject = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: JsonObject, path: str) -> "EntitySpec":
        try:
            entity_id = str(data["id"])
            kind = str(data["kind"])
            dimensions = _vec3(data["dimensions"], f"{path}.dimensions")
        except KeyError as error:
            raise SceneSpecError(f"{path}.{error.args[0]} is required") from error
        keyframes = tuple(
            Keyframe.from_dict(item, f"{path}.keyframes[{index}]")
            for index, item in enumerate(data.get("keyframes", []))
        )
        return cls(
            id=entity_id,
            name=str(data.get("name", entity_id)),
            kind=kind,
            dimensions=dimensions,
            color=_color(data.get("color", [0.72, 0.74, 0.78, 1.0]), f"{path}.color"),
            location=_vec3(data.get("location", [0, 0, 0]), f"{path}.location"),
            rotation=_vec3(data.get("rotation", [0, 0, 0]), f"{path}.rotation"),
            scale=_vec3(data.get("scale", [1, 1, 1]), f"{path}.scale"),
            keyframes=keyframes,
            metadata=dict(data.get("metadata", {})),
        )

    def to_dict(self) -> JsonObject:
        return {
            "id": self.id,
            "name": self.name,
            "kind": self.kind,
            "dimensions": list(self.dimensions),
            "color": list(self.color),
            "location": list(self.location),
            "rotation": list(self.rotation),
            "scale": list(self.scale),
            "keyframes": [keyframe.to_dict() for keyframe in self.keyframes],
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class CameraSpec:
    id: str = "camera"
    location: Vec3 = (6.0, -6.0, 4.0)
    rotation: Vec3 = (65.0, 0.0, 45.0)
    focal_length: float = 35.0
    target: str | None = None
    keyframes: tuple[Keyframe, ...] = ()

    @classmethod
    def from_dict(cls, data: JsonObject) -> "CameraSpec":
        return cls(
            id=str(data.get("id", "camera")),
            location=_vec3(data.get("location", [6, -6, 4]), "camera.location"),
            rotation=_vec3(data.get("rotation", [65, 0, 45]), "camera.rotation"),
            focal_length=float(data.get("focal_length", 35)),
            target=str(data["target"]) if data.get("target") is not None else None,
            keyframes=tuple(
                Keyframe.from_dict(item, f"camera.keyframes[{index}]")
                for index, item in enumerate(data.get("keyframes", []))
            ),
        )

    def to_dict(self) -> JsonObject:
        result: JsonObject = {
            "id": self.id,
            "location": list(self.location),
            "rotation": list(self.rotation),
            "focal_length": self.focal_length,
        }
        if self.target is not None:
            result["target"] = self.target
        result["keyframes"] = [keyframe.to_dict() for keyframe in self.keyframes]
        return result


@dataclass(frozen=True)
class Marker:
    time: float
    label: str

    @classmethod
    def from_dict(cls, data: JsonObject, path: str) -> "Marker":
        try:
            return cls(time=float(data["time"]), label=str(data["label"]))
        except KeyError as error:
            raise SceneSpecError(f"{path}.{error.args[0]} is required") from error

    def to_dict(self) -> JsonObject:
        return {"time": self.time, "label": self.label}


@dataclass(frozen=True)
class SceneSpec:
    version: str
    title: str
    duration_seconds: float
    fps: int
    resolution: tuple[int, int]
    world_color: Color
    entities: tuple[EntitySpec, ...]
    camera: CameraSpec
    markers: tuple[Marker, ...] = ()
    metadata: JsonObject = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: JsonObject) -> "SceneSpec":
        try:
            resolution_numbers = _numbers(data["resolution"], 2, "resolution")
            entities_data: Iterable[JsonObject] = data["entities"]
            camera_data: JsonObject = data["camera"]
            return cls(
                version=str(data["version"]),
                title=str(data["title"]),
                duration_seconds=float(data["duration_seconds"]),
                fps=int(data["fps"]),
                resolution=(int(resolution_numbers[0]), int(resolution_numbers[1])),
                world_color=_color(data.get("world_color", [0.025, 0.03, 0.04, 1]), "world_color"),
                entities=tuple(
                    EntitySpec.from_dict(item, f"entities[{index}]")
                    for index, item in enumerate(entities_data)
                ),
                camera=CameraSpec.from_dict(camera_data),
                markers=tuple(
                    Marker.from_dict(item, f"markers[{index}]")
                    for index, item in enumerate(data.get("markers", []))
                ),
                metadata=dict(data.get("metadata", {})),
            )
        except KeyError as error:
            raise SceneSpecError(f"{error.args[0]} is required") from error
        except TypeError as error:
            raise SceneSpecError("SceneSpec fields have invalid types") from error

    def to_dict(self) -> JsonObject:
        return {
            "version": self.version,
            "title": self.title,
            "duration_seconds": self.duration_seconds,
            "fps": self.fps,
            "resolution": list(self.resolution),
            "world_color": list(self.world_color),
            "entities": [entity.to_dict() for entity in self.entities],
            "camera": self.camera.to_dict(),
            "markers": [marker.to_dict() for marker in self.markers],
            "metadata": self.metadata,
        }


def load_scene(path: str | Path) -> SceneSpec:
    source = Path(path)
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise SceneSpecError(f"Could not read SceneSpec from {source}: {error}") from error
    if not isinstance(data, dict):
        raise SceneSpecError("SceneSpec root must be an object")
    return SceneSpec.from_dict(data)


def save_scene(scene: SceneSpec, path: str | Path) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(scene.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return destination
