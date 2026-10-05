# AI video handoff

PrevisForge does not force one video provider. The durable handoff is the local artifact bundle.

## Recommended workflow

1. Build and watch `preview.mp4` at full speed.
2. Fix blocking, collisions, exits from frame, timing, and focal length in `scene.json` or `scene.blend`.
3. Split a long sequence at story-beat markers when the target model has a short context window.
4. Render the first or strongest frame of each segment.
5. Send the whitebox video plus a style/character reference to a reference-to-video model.
6. Compare output motion with the whitebox before spending another generation.
7. Regenerate only the failing segment, then edit the accepted segments together.

## What the whitebox controls well

- shot size and broad composition;
- camera direction and speed;
- subject screen position;
- entrances, exits, obstacle avoidance, and approximate timing;
- continuity between adjacent generations.

## What it does not guarantee

- exact geometry preservation by a generative model;
- stable faces, hands, wardrobe, or fine prop identity;
- physically correct interaction;
- pixel-accurate camera matching;
- a successful single generation.

Treat the whitebox as a strong spatial reference, not as a deterministic renderer contract.

## Future control passes

The `.blend` source can produce model-specific control video without changing SceneSpec: depth, normals, object IDs, pose skeletons, optical flow, line art, masks, and per-subject beauty passes. These belong in renderer adapters because video models accept different combinations and encodings.
