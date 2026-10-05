# PrevisForge

Local-first 3D whitebox previsualization for controllable AI video.

PrevisForge turns a structured scene plan—or a natural-language brief through any OpenAI-compatible planner—into an editable Blender scene, a GLB transfer file, and a timed whitebox video. Use those artifacts as composition, camera, motion, depth, or reference guidance before spending credits on a generative video model.

> Status: **alpha / working MVP**. The local Blender pipeline is functional. The SceneSpec is intentionally small and versioned so editors, agents, and render adapters can grow around it.

## Why this exists

Text-to-video is good at appearance and weak at deterministic spatial direction. PrevisForge separates the jobs:

1. plan space, blocking, motion, and camera in a cheap editable 3D scene;
2. validate the plan before rendering;
3. export a control video and 3D scene;
4. let a video model handle materials, lighting, texture, and cinematic finish.

The whitebox is the source of spatial truth. The video model is the renderer, not the director.

## What works today

- Versioned JSON `SceneSpec`.
- Boxes, spheres, cylinders, torus shapes, planes, empty transforms, and simple actors.
- Object, actor, prop, and camera keyframes.
- Moving camera targets and focal-length animation.
- Story-beat timeline markers.
- Structural validation plus approximate overlap and camera-obstruction warnings.
- Headless Blender compilation.
- `.blend`, `.glb`, MP4 preview, poster, validation report, and artifact manifest.
- Offline demos and OpenAI-compatible LLM planning, including local endpoints such as Ollama.

## Requirements

- Python 3.11+
- Blender 4.5+ (tested with Blender 5.1.2)
- FFmpeg on `PATH`

No Python runtime dependency is required for the offline workflow.

## Quick start

```bash
git clone https://github.com/Pluviobyte/previsforge.git
cd previsforge
python3 -m pip install -e .

# Create an offline scene plan
previsforge plan --demo space-station --output scene.json

# Validate and inspect it
previsforge validate scene.json
previsforge inspect scene.json

# Build the editable whitebox and preview
previsforge build scene.json \
  --output-dir outputs/orbital-escape \
  --blender /Applications/Blender.app/Contents/MacOS/Blender
```

Linux and Windows users should pass the path to their Blender executable.

Generated files:

```text
outputs/orbital-escape/
├── scene.json        # portable source of truth
├── scene.blend       # editable Blender project
├── scene.glb         # interchange / web / engine handoff
├── preview.mp4       # timed whitebox control video
├── poster.png        # midpoint reference frame
├── validation.json   # deterministic checks
└── artifacts.json    # automation manifest
```

## Plan with a local or hosted LLM

PrevisForge supports the OpenAI Chat Completions request/response shape. For a local Ollama-compatible endpoint:

```bash
previsforge plan \
  "A cyclist enters a tunnel, avoids two barriers, and the camera cranes overhead" \
  --endpoint http://127.0.0.1:11434/v1 \
  --model your-local-model \
  --output cyclist.json
```

For an authenticated endpoint, put the key in `PREVISFORGE_API_KEY`. The key is read only for the request and is never included in generated files or logs.

## Use the result with AI video

Typical handoff options:

- upload `preview.mp4` as motion/composition reference;
- use `poster.png` as the first frame or style-transfer input;
- render extra views, depth, normals, masks, or character passes from `scene.blend`;
- import `scene.glb` into another 3D editor or web tool;
- generate several short clips per story-beat marker instead of forcing one long generation.

See [AI video handoff](docs/AI_VIDEO_HANDOFF.md) for a model-neutral workflow.

## Project design

- [Architecture](docs/ARCHITECTURE.md)
- [SceneSpec reference](docs/SCENE_SPEC.md)
- [Product requirements](docs/PRD.md)
- [Contributing](CONTRIBUTING.md)
- [Security](SECURITY.md)

## Tests

```bash
python3 -m unittest discover -v
```

The Blender end-to-end test runs when Blender is installed at the tested macOS path and otherwise skips. All other tests use only the Python standard library.

## Roadmap

- Browser timeline and Three.js viewport.
- Reusable asset registry and semantic scene templates.
- Navigation meshes and more accurate collision tests.
- Depth, normal, segmentation, pose, and optical-flow control passes.
- Rigged actor actions and text-to-motion adapters.
- Reference-image reconstruction and camera matching.
- Pluggable video-generation adapters without making any provider mandatory.

## License

MIT. See [LICENSE](LICENSE).
