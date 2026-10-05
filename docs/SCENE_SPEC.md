# SceneSpec 1.0

SceneSpec is the portable source of truth for a previsualization. Units are meters, time is seconds, rotations are XYZ Euler degrees, and colors are linear RGBA values in the range 0–1.

## Top-level fields

| Field | Meaning |
| --- | --- |
| `version` | Currently `1.0` |
| `title` | Human-readable project title |
| `duration_seconds` | Positive timeline duration |
| `fps` | Frames per second |
| `resolution` | `[width, height]` |
| `world_color` | Background RGBA |
| `entities` | Stable-ID scene objects |
| `camera` | Active camera definition |
| `markers` | Named story beats |
| `metadata` | Forward-compatible project metadata |

## Entity

Required fields are `id`, `kind`, and `dimensions`. The serializer writes the complete normalized form:

```json
{
  "id": "hero",
  "name": "Hero",
  "kind": "actor",
  "dimensions": [0.7, 0.7, 1.8],
  "color": [0.8, 0.8, 0.75, 1.0],
  "location": [0, 0, 0],
  "rotation": [0, 0, 0],
  "scale": [1, 1, 1],
  "keyframes": [
    {"time": 0, "location": [0, 0, 0]},
    {"time": 4, "location": [5, 0, 0]}
  ],
  "metadata": {"collision": true}
}
```

Supported kinds: `box`, `sphere`, `cylinder`, `torus`, `plane`, `actor`, and `empty`.

Recognized metadata:

- `collision: true`: include a static entity in approximate overlap checks.
- `camera_blocker: true`: warn when a camera path segment crosses its approximate bounds.
- `wireframe: true`: compile a box as a visible structural cage.

## Camera

The camera accepts the same transform keyframes plus `focal_length`. When `target` references an entity ID, Blender adds a tracking constraint and camera rotation becomes secondary.

```json
{
  "id": "camera",
  "location": [-6, -4, 2.5],
  "rotation": [65, 0, -45],
  "focal_length": 28,
  "target": "hero",
  "keyframes": [
    {"time": 0, "location": [-6, -4, 2.5], "focal_length": 28},
    {"time": 4, "location": [2, -4, 3], "focal_length": 35}
  ]
}
```

## Compatibility

Consumers must reject unsupported major/minor versions rather than silently guessing. New optional metadata may be added without changing version 1.0. Changes to required fields, coordinate conventions, or timing semantics require a new SceneSpec version.
