import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class CliContractTests(unittest.TestCase):
    def run_cli(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-m", "previsforge", *arguments],
            cwd=Path(__file__).parents[1],
            text=True,
            capture_output=True,
            check=False,
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


if __name__ == "__main__":
    unittest.main()
