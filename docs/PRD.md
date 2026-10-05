# PrevisForge MVP Product Requirements

## Goal

Create a reusable, open-source local previsualization pipeline for AI video production. A creator should be able to describe or author a scene, validate its spatial and temporal logic, build an editable Blender whitebox, and export control artifacts for downstream AI video generation.

## Public interfaces

The MVP exposes four stable CLI seams:

1. `plan`: turn a natural-language brief into a SceneSpec JSON document through an OpenAI-compatible endpoint, with a deterministic built-in demo planner for offline use.
2. `validate`: validate SceneSpec structure, references, timing, animation tracks, and basic spatial safety rules without launching Blender.
3. `build`: invoke Blender headlessly to create an editable `.blend`, export `.glb`, and render a whitebox preview.
4. `inspect`: summarize a SceneSpec and list its expected artifacts in machine-readable JSON.

## SceneSpec requirements

- Versioned JSON format.
- Project settings: duration, FPS, resolution, and world background.
- Reusable primitive and actor entities with stable IDs.
- Keyframed position, Euler rotation, and scale tracks.
- A camera with keyframed transforms, focal length, and an optional moving target.
- Named markers for story beats.
- Forward-compatible metadata.

## Validation requirements

- Reject duplicate IDs, missing references, invalid dimensions, out-of-range keyframes, and non-monotonic tracks.
- Warn about static overlaps and camera paths that cross static geometry.
- Produce deterministic JSON reports and non-zero exit codes for errors.

## Build requirements

- Blender is the canonical scene compiler.
- Create editable collections, named objects, materials, animation curves, camera, lights, and timeline markers.
- Export `scene.blend`, `scene.glb`, `preview.mp4`, `poster.png`, `validation.json`, and `artifacts.json`.
- Building must not require a hosted service or proprietary asset.

## Open-source requirements

- MIT license.
- No secrets or paid-service dependency required for the offline demo.
- Contributor, security, architecture, SceneSpec, and AI-video handoff documentation.
- Automated tests for the four public CLI seams.

## Non-goals for MVP

- Photorealistic rendering.
- Automatic generation of production-ready character meshes.
- A browser-based timeline editor.
- Guaranteed obedience by downstream generative video models.
- Arbitrary natural-language scene generation without an LLM endpoint.

## Acceptance scenario

From a clean checkout on a machine with Blender, a user can run the offline space-station demo, validate it, build a 3D whitebox animation, and receive all documented artifacts. The same engine must also accept a materially different example scene without code changes.
