"""Deterministic offline scenes that exercise the complete pipeline."""

from __future__ import annotations

from copy import deepcopy

from .model import SceneSpec


SPACE_STATION: dict[str, object] = {
    "version": "1.0",
    "title": "Orbital Escape",
    "duration_seconds": 12,
    "fps": 15,
    "resolution": [640, 360],
    "world_color": [0.012, 0.018, 0.032, 1.0],
    "entities": [
        {
            "id": "maintenance_bay",
            "name": "Maintenance bay",
            "kind": "box",
            "dimensions": [7, 5, 3.5],
            "color": [0.55, 0.58, 0.62, 0.22],
            "location": [-6.5, 0, 1.75],
            "rotation": [0, 0, 0],
            "scale": [1, 1, 1],
            "keyframes": [],
            "metadata": {"wireframe": True, "collision": False},
        },
        {
            "id": "cargo_tunnel",
            "name": "Cargo tunnel",
            "kind": "box",
            "dimensions": [7, 3.5, 3.2],
            "color": [0.65, 0.68, 0.72, 0.18],
            "location": [0.5, 0, 1.6],
            "rotation": [0, 0, 0],
            "scale": [1, 1, 1],
            "keyframes": [],
            "metadata": {"wireframe": True, "collision": False},
        },
        {
            "id": "habitat_ring",
            "name": "Rotating habitat",
            "kind": "torus",
            "dimensions": [8, 8, 1.2],
            "color": [0.72, 0.74, 0.78, 1],
            "location": [6, 0, 2.2],
            "rotation": [90, 0, 0],
            "scale": [1, 1, 1],
            "keyframes": [
                {"time": 0, "rotation": [90, 0, 0]},
                {"time": 12, "rotation": [90, 0, 120]},
            ],
            "metadata": {"collision": False},
        },
        {
            "id": "airlock",
            "name": "Airlock",
            "kind": "torus",
            "dimensions": [3.5, 3.5, 0.8],
            "color": [0.5, 0.54, 0.6, 1],
            "location": [11, 0, 2],
            "rotation": [90, 0, 0],
            "scale": [1, 1, 1],
            "keyframes": [],
            "metadata": {"collision": False},
        },
        {
            "id": "escape_capsule",
            "name": "Escape capsule",
            "kind": "box",
            "dimensions": [3.5, 3.5, 3.5],
            "color": [0.78, 0.8, 0.82, 1],
            "location": [14, 0, 2],
            "rotation": [0, 0, 0],
            "scale": [1, 1, 1],
            "keyframes": [],
            "metadata": {"wireframe": True, "collision": False},
        },
        {
            "id": "cargo_a",
            "name": "Floating cargo A",
            "kind": "box",
            "dimensions": [1.1, 1.1, 1.1],
            "color": [0.9, 0.48, 0.12, 1],
            "location": [-1, -0.8, 1.5],
            "rotation": [10, 0, 15],
            "scale": [1, 1, 1],
            "keyframes": [
                {"time": 0, "location": [-1, -0.8, 1.5], "rotation": [10, 0, 15]},
                {"time": 6, "location": [0, 0.8, 2.3], "rotation": [80, 35, 120]},
                {"time": 12, "location": [1, -0.2, 1.2], "rotation": [160, 80, 250]},
            ],
            "metadata": {"collision": True},
        },
        {
            "id": "cargo_b",
            "name": "Floating cargo B",
            "kind": "box",
            "dimensions": [0.7, 0.9, 0.7],
            "color": [0.18, 0.5, 0.78, 1],
            "location": [1.5, 0.9, 2.1],
            "rotation": [0, 20, 0],
            "scale": [1, 1, 1],
            "keyframes": [
                {"time": 0, "location": [1.5, 0.9, 2.1]},
                {"time": 12, "location": [0.2, -0.8, 1.5], "rotation": [120, 40, 180]},
            ],
            "metadata": {"collision": True},
        },
        {
            "id": "astronaut",
            "name": "Astronaut",
            "kind": "actor",
            "dimensions": [0.7, 0.7, 1.8],
            "color": [0.82, 0.82, 0.76, 1],
            "location": [-9, 0, 1.2],
            "rotation": [0, 0, 0],
            "scale": [1, 1, 1],
            "keyframes": [
                {"time": 0, "location": [-9, 0, 1.2]},
                {"time": 3, "location": [-3, 0.7, 1.5], "rotation": [0, 0, -10]},
                {"time": 6, "location": [4.5, 0, 2.2], "rotation": [0, 0, 0]},
                {"time": 9, "location": [10.5, 0, 2], "rotation": [0, 0, 15]},
                {"time": 12, "location": [14, 0, 2]},
            ],
            "metadata": {"collision": True},
        },
        {
            "id": "guide_drone",
            "name": "Guide drone",
            "kind": "sphere",
            "dimensions": [0.45, 0.45, 0.45],
            "color": [0.05, 0.9, 1, 1],
            "location": [-7.8, 0, 2.2],
            "rotation": [0, 0, 0],
            "scale": [1, 1, 1],
            "keyframes": [
                {"time": 0, "location": [-7.8, 0, 2.2]},
                {"time": 3, "location": [-1.8, 0.2, 2.5]},
                {"time": 6, "location": [5.8, 0, 3]},
                {"time": 9, "location": [11.8, 0, 2.7]},
                {"time": 12, "location": [15, 0, 2.8]},
            ],
            "metadata": {"collision": False},
        },
    ],
    "camera": {
        "id": "camera",
        "location": [-12, -6, 3.8],
        "rotation": [70, 0, -65],
        "focal_length": 28,
        "target": "astronaut",
        "keyframes": [
            {"time": 0, "location": [-12, -6, 3.8], "focal_length": 28},
            {"time": 3, "location": [-5.5, -4, 2.8], "focal_length": 24},
            {"time": 6, "location": [1.5, -4, 3.2], "focal_length": 24},
            {"time": 9, "location": [7.5, -4.5, 3], "focal_length": 28},
            {"time": 12, "location": [11, -5, 3.2], "focal_length": 32},
        ],
    },
    "markers": [
        {"time": 0, "label": "Enter maintenance bay"},
        {"time": 3, "label": "Avoid cargo"},
        {"time": 6, "label": "Cross habitat ring"},
        {"time": 9, "label": "Enter airlock"},
        {"time": 12, "label": "Reach escape capsule"},
    ],
    "metadata": {"template": "space-station", "units": "meters"},
}


PRODUCT_ORBIT: dict[str, object] = {
    "version": "1.0",
    "title": "Product Orbit",
    "duration_seconds": 6,
    "fps": 24,
    "resolution": [640, 360],
    "world_color": [0.025, 0.025, 0.03, 1],
    "entities": [
        {"id": "floor", "name": "Floor", "kind": "cylinder", "dimensions": [6, 6, 0.3], "color": [0.18, 0.18, 0.2, 1], "location": [0, 0, -0.15], "rotation": [0, 0, 0], "scale": [1, 1, 1], "keyframes": [], "metadata": {"collision": False}},
        {"id": "product", "name": "Product", "kind": "box", "dimensions": [1.2, 1.2, 2.2], "color": [0.85, 0.86, 0.9, 1], "location": [0, 0, 1.1], "rotation": [0, 0, 0], "scale": [1, 1, 1], "keyframes": [{"time": 0, "rotation": [0, 0, 0]}, {"time": 6, "rotation": [0, 0, 360]}], "metadata": {"collision": True}},
    ],
    "camera": {"id": "camera", "location": [5, -5, 3], "rotation": [65, 0, 45], "focal_length": 50, "target": "product", "keyframes": [{"time": 0, "location": [5, -5, 3]}, {"time": 3, "location": [-5, -5, 2.5]}, {"time": 6, "location": [-5, 5, 3]}]},
    "markers": [{"time": 0, "label": "Reveal"}, {"time": 3, "label": "Hero angle"}, {"time": 6, "label": "End frame"}],
    "metadata": {"template": "product-orbit", "units": "meters"},
}


TEMPLATES = {"space-station": SPACE_STATION, "product-orbit": PRODUCT_ORBIT}


def create_demo(name: str) -> SceneSpec:
    try:
        return SceneSpec.from_dict(deepcopy(TEMPLATES[name]))
    except KeyError as error:
        choices = ", ".join(sorted(TEMPLATES))
        raise ValueError(f"Unknown demo '{name}'. Choose one of: {choices}") from error
