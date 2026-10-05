# Architecture

## Design principle

PrevisForge separates creative intent from 3D execution. The portable `SceneSpec` is the contract between planners, editors, validators, Blender, and downstream video tools.

```text
Natural-language brief or editor
             │
             ▼
      Planner adapter
             │
             ▼
        SceneSpec JSON ─────► Static validator
             │                      │
             ▼                      ▼
      Blender compiler       validation.json
             │
      ┌──────┼─────────┐
      ▼      ▼         ▼
   .blend   .glb   preview/poster
      │                  │
      └──────────┬───────┘
                 ▼
        AI video generation
```

## Modules

- `model.py`: immutable, versioned domain objects and JSON serialization.
- `validation.py`: deterministic checks that do not need Blender.
- `planning.py`: optional OpenAI-compatible text-to-SceneSpec adapter.
- `templates.py`: deterministic offline demonstrations and test fixtures.
- `build.py`: host-side process orchestration and artifact manifest.
- `blender_runtime.py`: Blender-only scene compiler and renderer.
- `inspection.py`: concise machine-readable scene summaries.
- `cli.py`: thin command adapters over the library.

## Why Blender

Blender provides editable geometry, animation, camera optics, interchange export, rendering, and a stable Python surface without making the project depend on a proprietary editor. The Blender runtime is isolated so normal validation and planning do not need `bpy` installed in the host interpreter.

## Trust boundaries

SceneSpec files and LLM responses are untrusted input. The current compiler maps data to a fixed set of operations and does not execute code from the scene file. API keys are read from a named environment variable and never serialized.

Blender is launched as a child process with explicit input and output paths. The compiler writes only inside the selected output directory.

## Extension points

- Add a planner by returning a valid `SceneSpec`.
- Add geometry kinds in both `validation.SUPPORTED_KINDS` and `blender_runtime.add_primitive`.
- Add a renderer by consuming SceneSpec or GLB and emitting entries for the manifest.
- Add an editor by reading and writing SceneSpec instead of reaching into Blender internals.
- Add video providers after the local artifacts exist; providers must not become required for building a whitebox.
