"""Blender process orchestration and artifact manifest generation."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
from typing import Any

from .model import load_scene, save_scene
from .validation import validate_scene


class BuildError(RuntimeError):
    """Raised when the Blender compiler fails."""


def build_scene(
    scene_path: str | Path,
    output_dir: str | Path,
    blender_path: str | Path,
) -> dict[str, Any]:
    source = Path(scene_path).resolve()
    destination = Path(output_dir).resolve()
    blender = Path(blender_path).resolve()
    if not blender.exists():
        raise BuildError(f"Blender executable not found: {blender}")

    scene = load_scene(source)
    report = validate_scene(scene)
    destination.mkdir(parents=True, exist_ok=True)
    save_scene(scene, destination / "scene.json")
    validation_path = destination / "validation.json"
    validation_path.write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if not report.valid:
        raise BuildError(f"SceneSpec has {len(report.errors)} validation error(s)")

    runtime = Path(__file__).with_name("blender_runtime.py")
    command = [
        str(blender),
        "--background",
        "--python",
        str(runtime),
        "--",
        "--scene",
        str(source),
        "--output-dir",
        str(destination),
    ]
    completed = subprocess.run(command, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        log = "\n".join((completed.stdout + completed.stderr).splitlines()[-30:])
        raise BuildError(f"Blender build failed:\n{log}")

    blender_outputs = ("scene.blend", "scene.glb", "poster.png")
    missing_blender_outputs = [name for name in blender_outputs if not (destination / name).is_file()]
    if missing_blender_outputs:
        log = "\n".join((completed.stdout + completed.stderr).splitlines()[-30:])
        raise BuildError(
            f"Blender did not create expected artifacts: {', '.join(missing_blender_outputs)}\n{log}"
        )

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise BuildError("ffmpeg is required to encode preview.mp4")
    frames_dir = destination / ".frames"
    preview_path = destination / "preview.mp4"
    encode = subprocess.run(
        [
            ffmpeg,
            "-y",
            "-loglevel",
            "error",
            "-framerate",
            str(scene.fps),
            "-i",
            str(frames_dir / "frame_%04d.png"),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(preview_path),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    if encode.returncode != 0:
        raise BuildError(f"ffmpeg encoding failed: {encode.stderr.strip()}")
    shutil.rmtree(frames_dir, ignore_errors=True)

    artifact_names = ("scene.json", "scene.blend", "scene.glb", "preview.mp4", "poster.png", "validation.json")
    missing = [name for name in artifact_names if not (destination / name).is_file()]
    if missing:
        raise BuildError(f"Blender did not create expected artifacts: {', '.join(missing)}")
    manifest = {
        "schema_version": "1.0",
        "status": "complete",
        "source": "scene.json",
        "artifacts": [
            {
                "name": name,
                "path": str(destination / name),
                "bytes": (destination / name).stat().st_size,
            }
            for name in artifact_names
        ],
    }
    (destination / "artifacts.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest
