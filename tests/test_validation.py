import unittest

from previsforge.model import SceneSpec
from previsforge.validation import validate_scene


def base_scene() -> dict:
    return {
        "version": "1.0",
        "title": "Validation fixture",
        "duration_seconds": 5,
        "fps": 24,
        "resolution": [640, 360],
        "world_color": [0, 0, 0, 1],
        "entities": [
            {
                "id": "hero",
                "name": "Hero",
                "kind": "actor",
                "dimensions": [0.6, 0.6, 1.8],
                "color": [0.8, 0.5, 0.2, 1],
                "location": [0, 0, 0],
                "rotation": [0, 0, 0],
                "scale": [1, 1, 1],
                "keyframes": [],
                "metadata": {},
            }
        ],
        "camera": {
            "id": "camera",
            "location": [4, -4, 2],
            "rotation": [65, 0, 45],
            "focal_length": 35,
            "target": "hero",
            "keyframes": [],
        },
        "markers": [],
        "metadata": {},
    }


class ValidationContractTests(unittest.TestCase):
    def test_reports_duplicate_ids_missing_target_and_bad_keyframes(self) -> None:
        source = base_scene()
        duplicate = dict(source["entities"][0])
        duplicate["keyframes"] = [
            {"time": 4, "location": [1, 0, 0]},
            {"time": 2, "location": [2, 0, 0]},
            {"time": 8, "location": [3, 0, 0]},
        ]
        source["entities"].append(duplicate)
        source["camera"]["target"] = "missing"

        report = validate_scene(SceneSpec.from_dict(source))

        self.assertFalse(report.valid)
        self.assertEqual(
            {finding.code for finding in report.errors},
            {"duplicate_id", "missing_camera_target", "keyframes_not_monotonic", "keyframe_out_of_range"},
        )
        self.assertEqual(report.to_dict()["summary"]["errors"], 4)

    def test_warns_when_static_objects_overlap_or_camera_crosses_a_blocker(self) -> None:
        source = base_scene()
        source["entities"][0]["location"] = [5, 0, 1]
        source["entities"][0]["metadata"] = {"collision": False}
        source["entities"].extend(
            [
                {"id": "box_a", "name": "A", "kind": "box", "dimensions": [2, 2, 2], "color": [1, 1, 1, 1], "location": [0, 0, 1], "rotation": [0, 0, 0], "scale": [1, 1, 1], "keyframes": [], "metadata": {"collision": True, "camera_blocker": True}},
                {"id": "box_b", "name": "B", "kind": "box", "dimensions": [2, 2, 2], "color": [1, 1, 1, 1], "location": [0.5, 0, 1], "rotation": [0, 0, 0], "scale": [1, 1, 1], "keyframes": [], "metadata": {"collision": True}},
            ]
        )
        source["camera"]["location"] = [-4, 0, 1]
        source["camera"]["target"] = "hero"
        source["camera"]["keyframes"] = [
            {"time": 0, "location": [-4, 0, 1]},
            {"time": 5, "location": [4, 0, 1]},
        ]

        report = validate_scene(SceneSpec.from_dict(source))
        warning_codes = {finding.code for finding in report.warnings}

        self.assertTrue(report.valid)
        self.assertIn("static_overlap", warning_codes)
        self.assertIn("camera_path_obstructed", warning_codes)


if __name__ == "__main__":
    unittest.main()
