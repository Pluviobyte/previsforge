import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class CliContractTests(unittest.TestCase):
    def run_cli(self, *arguments: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-m", "previsforge", *arguments],
            cwd=Path(__file__).parents[1],
            text=True,
            capture_output=True,
            check=False,
            env=env,
        )

    def test_offline_plan_creates_a_valid_reusable_scene(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            scene_path = Path(directory) / "station.json"
            plan = self.run_cli("plan", "--demo", "space-station", "--output", str(scene_path))
            validation = self.run_cli("validate", str(scene_path))
            inspection = self.run_cli("inspect", str(scene_path))

            self.assertEqual(plan.returncode, 0, plan.stderr)
            self.assertEqual(validation.returncode, 0, validation.stdout + validation.stderr)
            self.assertEqual(inspection.returncode, 0, inspection.stderr)
            self.assertTrue(scene_path.exists())
            self.assertTrue(json.loads(validation.stdout)["valid"])
            summary = json.loads(inspection.stdout)

        self.assertEqual(summary["title"], "Orbital Escape")
        self.assertGreaterEqual(summary["entities"], 8)
        self.assertGreaterEqual(summary["animated_entities"], 3)
        self.assertIn("scene.glb", summary["expected_artifacts"])

    def test_build_creates_editable_and_ai_handoff_artifacts(self) -> None:
        blender = Path("/Applications/Blender.app/Contents/MacOS/Blender")
        if not blender.exists():
            self.skipTest("Blender is not installed")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            scene_path = root / "product.json"
            output_dir = root / "build"
            plan = self.run_cli("plan", "--demo", "product-orbit", "--output", str(scene_path))
            build = self.run_cli(
                "build",
                str(scene_path),
                "--output-dir",
                str(output_dir),
                "--blender",
                str(blender),
            )

            self.assertEqual(plan.returncode, 0, plan.stderr)
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            manifest = json.loads((output_dir / "artifacts.json").read_text(encoding="utf-8"))
            for name in ("scene.json", "scene.blend", "scene.glb", "preview.mp4", "poster.png", "validation.json"):
                self.assertGreater((output_dir / name).stat().st_size, 0, name)
            self.assertEqual(manifest["status"], "complete")
            self.assertEqual({item["name"] for item in manifest["artifacts"]}, {
                "scene.json", "scene.blend", "scene.glb", "preview.mp4", "poster.png", "validation.json"
            })

    def test_build_cli_contract_runs_on_ci_with_tool_adapters(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tools = root / "tools"
            tools.mkdir()
            fake_blender = tools / "blender"
            fake_blender.write_text(
                "#!/usr/bin/env python3\n"
                "import pathlib, sys\n"
                "out = pathlib.Path(sys.argv[sys.argv.index('--output-dir') + 1])\n"
                "out.mkdir(parents=True, exist_ok=True)\n"
                "(out / '.frames').mkdir(exist_ok=True)\n"
                "for name in ('scene.blend', 'scene.glb', 'poster.png'):\n"
                "    (out / name).write_bytes(b'artifact')\n"
                "(out / '.frames' / 'frame_0001.png').write_bytes(b'frame')\n",
                encoding="utf-8",
            )
            fake_blender.chmod(0o755)
            fake_ffmpeg = tools / "ffmpeg"
            fake_ffmpeg.write_text(
                "#!/usr/bin/env python3\n"
                "import pathlib, sys\n"
                "pathlib.Path(sys.argv[-1]).write_bytes(b'preview')\n",
                encoding="utf-8",
            )
            fake_ffmpeg.chmod(0o755)
            scene_path = root / "scene.json"
            output_dir = root / "output"
            self.assertEqual(
                self.run_cli("plan", "--demo", "product-orbit", "--output", str(scene_path)).returncode,
                0,
            )
            environment = dict(os.environ)
            environment["PATH"] = str(tools) + os.pathsep + environment.get("PATH", "")

            build = self.run_cli(
                "build",
                str(scene_path),
                "--output-dir",
                str(output_dir),
                "--blender",
                str(fake_blender),
                env=environment,
            )

            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            self.assertEqual(json.loads(build.stdout)["status"], "complete")


if __name__ == "__main__":
    unittest.main()
