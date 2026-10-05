# Contributing

Contributions are welcome.

1. Open an issue describing the user-facing behavior and SceneSpec impact.
2. Keep Blender-only imports inside the Blender runtime adapter.
3. Add a failing public-interface test before implementation when changing one of the documented seams.
4. Run `python3 -m unittest discover -v`.
5. Update the SceneSpec and architecture docs for contract changes.

Do not commit generated renders, API keys, paid assets, or media without redistribution rights.
