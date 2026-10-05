# Coding Standards

- Python 3.11+ and standard library first; Blender-only imports stay inside the Blender runtime adapter.
- Public functions and data structures use type hints.
- Domain validation returns structured findings instead of printing or exiting.
- CLI commands are thin adapters over importable library functions.
- Filesystem writes must be explicit and scoped to a caller-provided output path.
- Tests exercise public APIs or the CLI; they do not mock private implementation details.
- Keep the SceneSpec format versioned and deterministic.
- Never log API keys, full authorization headers, or unrelated environment variables.
