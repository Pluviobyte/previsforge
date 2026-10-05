"""Command-line interface for PrevisForge."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

from .inspection import inspect_scene
from .build import BuildError, build_scene
from .model import SceneSpecError, load_scene, save_scene
from .planning import PlanningError, plan_scene
from .templates import TEMPLATES, create_demo
from .validation import validate_scene


def _json_print(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="previsforge",
        description="Local-first whitebox previsualization for AI video.",
    )
    parser.add_argument("--version", action="version", version="PrevisForge 0.1.0")
    commands = parser.add_subparsers(dest="command", required=True)

    plan = commands.add_parser("plan", help="Create a SceneSpec.")
    plan.add_argument("prompt", nargs="?", help="Natural-language scene brief.")
    plan.add_argument("--demo", choices=sorted(TEMPLATES), help="Use an offline demo planner.")
    plan.add_argument("--output", type=Path, required=True)
    plan.add_argument("--endpoint", help="OpenAI-compatible API root, e.g. http://localhost:11434/v1")
    plan.add_argument("--model", help="Planner model name.")
    plan.add_argument("--api-key-env", default="PREVISFORGE_API_KEY", help="Environment variable containing the API key.")

    validate = commands.add_parser("validate", help="Validate a SceneSpec.")
    validate.add_argument("scene", type=Path)
    validate.add_argument("--output", type=Path)

    inspect = commands.add_parser("inspect", help="Inspect a SceneSpec.")
    inspect.add_argument("scene", type=Path)

    build = commands.add_parser("build", help="Compile a SceneSpec with Blender.")
    build.add_argument("scene", type=Path)
    build.add_argument("--output-dir", type=Path, required=True)
    build.add_argument("--blender", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "plan":
            if args.demo:
                scene = create_demo(args.demo)
            else:
                if not args.prompt or not args.endpoint or not args.model:
                    parser.error("plan requires --demo, or PROMPT with --endpoint and --model")
                scene = plan_scene(
                    args.prompt,
                    endpoint=args.endpoint,
                    model=args.model,
                    api_key=os.environ.get(args.api_key_env),
                )
            save_scene(scene, args.output)
            _json_print({"status": "created", "path": str(args.output), "title": scene.title})
            return 0
        if args.command == "validate":
            report = validate_scene(load_scene(args.scene))
            data = report.to_dict()
            if args.output:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            _json_print(data)
            return 0 if report.valid else 2
        if args.command == "inspect":
            _json_print(inspect_scene(load_scene(args.scene)))
            return 0
        if args.command == "build":
            _json_print(build_scene(args.scene, args.output_dir, args.blender))
            return 0
    except (BuildError, PlanningError, SceneSpecError, ValueError, OSError) as error:
        _json_print({"status": "error", "message": str(error)})
        return 2
    return 2


if __name__ == "__main__":
    sys.exit(main())
