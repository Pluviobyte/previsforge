"""Public inspection helpers for editor and automation integrations."""

from __future__ import annotations

from .model import SceneSpec


EXPECTED_ARTIFACTS = (
    "scene.json",
    "scene.blend",
    "scene.glb",
    "preview.mp4",
    "poster.png",
    "validation.json",
    "artifacts.json",
)


def inspect_scene(scene: SceneSpec) -> dict[str, object]:
    animated = sum(bool(entity.keyframes) for entity in scene.entities)
    return {
        "version": scene.version,
        "title": scene.title,
        "duration_seconds": scene.duration_seconds,
        "fps": scene.fps,
        "frames": round(scene.duration_seconds * scene.fps),
        "resolution": list(scene.resolution),
        "entities": len(scene.entities),
        "animated_entities": animated,
        "camera_keyframes": len(scene.camera.keyframes),
        "markers": len(scene.markers),
        "expected_artifacts": list(EXPECTED_ARTIFACTS),
    }
