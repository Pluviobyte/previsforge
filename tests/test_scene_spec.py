import json
import tempfile
import unittest
from pathlib import Path

from previsforge.model import SceneSpec, load_scene, save_scene


class SceneSpecContractTests(unittest.TestCase):
    def test_scene_spec_round_trips_without_losing_domain_data(self) -> None:
        source = {
            "version": "1.0",
            "title": "Product reveal",
            "duration_seconds": 6,
            "fps": 24,
            "resolution": [640, 360],
            "world_color": [0.02, 0.03, 0.05, 1.0],
            "entities": [
                {
                    "id": "product",
                    "name": "Hero product",
                    "kind": "box",
                    "dimensions": [1, 1, 2],
                    "color": [0.7, 0.7, 0.72, 1],
                    "location": [0, 0, 1],
                    "rotation": [0, 0, 0],
                    "scale": [1, 1, 1],
                    "keyframes": [
                        {"time": 0, "rotation": [0, 0, 0]},
                        {"time": 6, "rotation": [0, 0, 360]},
                    ],
                    "metadata": {"collision": True},
                }
            ],
            "camera": {
                "id": "camera",
                "location": [4, -4, 2.5],
                "rotation": [65, 0, 45],
                "focal_length": 50,
                "target": "product",
                "keyframes": [{"time": 3, "focal_length": 70}],
            },
            "markers": [{"time": 0, "label": "Reveal"}],
            "metadata": {"aspect": "16:9"},
        }

        scene = SceneSpec.from_dict(source)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "scene.json"
            save_scene(scene, path)
            loaded = load_scene(path)
            encoded = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(loaded, scene)
        self.assertEqual(encoded, source)


if __name__ == "__main__":
    unittest.main()
