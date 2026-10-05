"""Blender-side SceneSpec compiler.

This module is launched by Blender, not by the host Python interpreter.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys

import bpy


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scene", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    arguments = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    return parser.parse_args(arguments)


def radians(values: list[float]) -> tuple[float, float, float]:
    return tuple(math.radians(value) for value in values)


def reset_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for collection in tuple(bpy.data.collections):
        if collection.name != "Collection":
            bpy.data.collections.remove(collection)


def material_for(entity: dict) -> bpy.types.Material:
    material = bpy.data.materials.new(f"MAT_{entity['id']}")
    color = entity.get("color", [0.72, 0.74, 0.78, 1])
    material.diffuse_color = color
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    if shader:
        shader.inputs["Base Color"].default_value = color
        shader.inputs["Roughness"].default_value = 0.72
        shader.inputs["Metallic"].default_value = 0.05
    return material


def apply_base_transform(obj: bpy.types.Object, entity: dict) -> None:
    obj.location = entity.get("location", [0, 0, 0])
    obj.rotation_mode = "XYZ"
    obj.rotation_euler = radians(entity.get("rotation", [0, 0, 0]))
    obj.scale = entity.get("scale", [1, 1, 1])


def apply_animation(obj: bpy.types.Object, entity: dict, fps: int) -> None:
    for keyframe in entity.get("keyframes", []):
        frame = round(float(keyframe["time"]) * fps) + 1
        if "location" in keyframe:
            obj.location = keyframe["location"]
            obj.keyframe_insert("location", frame=frame)
        if "rotation" in keyframe:
            obj.rotation_euler = radians(keyframe["rotation"])
            obj.keyframe_insert("rotation_euler", frame=frame)
        if "scale" in keyframe:
            obj.scale = keyframe["scale"]
            obj.keyframe_insert("scale", frame=frame)


def add_primitive(entity: dict, material: bpy.types.Material) -> bpy.types.Object:
    kind = entity["kind"]
    dimensions = entity["dimensions"]
    if kind == "box":
        bpy.ops.mesh.primitive_cube_add(size=1)
    elif kind == "sphere":
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.5)
    elif kind == "cylinder":
        bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.5, depth=1)
    elif kind == "torus":
        major = max(dimensions[0], dimensions[1]) * 0.5 - dimensions[2] * 0.25
        minor = dimensions[2] * 0.25
        bpy.ops.mesh.primitive_torus_add(major_radius=max(major, minor), minor_radius=minor)
    elif kind == "plane":
        bpy.ops.mesh.primitive_plane_add(size=1)
    elif kind == "empty":
        bpy.ops.object.empty_add(type="PLAIN_AXES")
    else:
        raise ValueError(f"Unsupported primitive kind: {kind}")
    obj = bpy.context.object
    obj.name = entity["id"]
    if kind not in {"torus", "empty"}:
        obj.dimensions = dimensions
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if obj.data and hasattr(obj.data, "materials"):
        obj.data.materials.append(material)
    if entity.get("metadata", {}).get("wireframe") and kind == "box":
        modifier = obj.modifiers.new("WhiteboxEdges", "WIREFRAME")
        modifier.thickness = 0.035
    return obj


def add_actor(entity: dict, material: bpy.types.Material) -> bpy.types.Object:
    bpy.ops.object.empty_add(type="PLAIN_AXES")
    root = bpy.context.object
    root.name = entity["id"]
    height = float(entity["dimensions"][2])

    bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=12, radius=height * 0.14)
    head = bpy.context.object
    head.name = f"{entity['id']}_head"
    head.location = (0, 0, height * 0.84)
    head.parent = root
    head.data.materials.append(material)

    bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=height * 0.14, depth=height * 0.5)
    body = bpy.context.object
    body.name = f"{entity['id']}_body"
    body.location = (0, 0, height * 0.48)
    body.parent = root
    body.data.materials.append(material)

    for side in (-1, 1):
        bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=height * 0.045, depth=height * 0.48)
        leg = bpy.context.object
        leg.name = f"{entity['id']}_leg_{side}"
        leg.location = (side * height * 0.075, 0, height * 0.08)
        leg.parent = root
        leg.data.materials.append(material)
    return root


def add_entity(entity: dict, fps: int) -> bpy.types.Object:
    material = material_for(entity)
    obj = add_actor(entity, material) if entity["kind"] == "actor" else add_primitive(entity, material)
    apply_base_transform(obj, entity)
    apply_animation(obj, entity, fps)
    obj["previsforge_kind"] = entity["kind"]
    obj["previsforge_name"] = entity.get("name", entity["id"])
    return obj


def add_camera(spec: dict, objects: dict[str, bpy.types.Object], fps: int) -> bpy.types.Object:
    data = bpy.data.cameras.new(spec.get("id", "camera"))
    camera = bpy.data.objects.new(spec.get("id", "camera"), data)
    bpy.context.scene.collection.objects.link(camera)
    camera.location = spec.get("location", [6, -6, 4])
    camera.rotation_mode = "XYZ"
    camera.rotation_euler = radians(spec.get("rotation", [65, 0, 45]))
    data.lens = float(spec.get("focal_length", 35))
    for keyframe in spec.get("keyframes", []):
        frame = round(float(keyframe["time"]) * fps) + 1
        if "location" in keyframe:
            camera.location = keyframe["location"]
            camera.keyframe_insert("location", frame=frame)
        if "rotation" in keyframe:
            camera.rotation_euler = radians(keyframe["rotation"])
            camera.keyframe_insert("rotation_euler", frame=frame)
        if "focal_length" in keyframe:
            data.lens = float(keyframe["focal_length"])
            data.keyframe_insert("lens", frame=frame)
    target = spec.get("target")
    if target:
        constraint = camera.constraints.new(type="DAMPED_TRACK")
        constraint.target = objects[target]
        constraint.track_axis = "TRACK_NEGATIVE_Z"
    return camera


def add_lighting() -> None:
    world = bpy.context.scene.world or bpy.data.worlds.new("World")
    bpy.context.scene.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.35

    sun_data = bpy.data.lights.new("KeySun", type="SUN")
    sun_data.energy = 2.2
    sun = bpy.data.objects.new("KeySun", sun_data)
    bpy.context.scene.collection.objects.link(sun)
    sun.rotation_euler = radians([25, -20, -35])

    area_data = bpy.data.lights.new("Softbox", type="AREA")
    area_data.energy = 900
    area_data.shape = "DISK"
    area_data.size = 8
    area = bpy.data.objects.new("Softbox", area_data)
    bpy.context.scene.collection.objects.link(area)
    area.location = (0, -5, 8)
    area.rotation_euler = radians([25, 0, 0])


def configure_scene(spec: dict, output_dir: Path) -> None:
    scene = bpy.context.scene
    fps = int(spec["fps"])
    scene.frame_start = 1
    scene.frame_end = round(float(spec["duration_seconds"]) * fps) + 1
    scene.render.fps = fps
    scene.render.resolution_x = int(spec["resolution"][0])
    scene.render.resolution_y = int(spec["resolution"][1])
    scene.render.resolution_percentage = 100
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.film_transparent = False
    scene.render.filepath = str(output_dir / "poster.png")
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"

    world_color = spec.get("world_color", [0.025, 0.03, 0.04, 1])
    scene.world.color = world_color[:3]
    if scene.world.use_nodes:
        scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = world_color

    for marker in spec.get("markers", []):
        frame = round(float(marker["time"]) * fps) + 1
        scene.timeline_markers.new(marker["label"], frame=frame)


def render_artifacts(spec: dict, output_dir: Path) -> None:
    scene = bpy.context.scene
    midpoint = round((scene.frame_start + scene.frame_end) / 2)
    scene.frame_set(midpoint)
    scene.render.filepath = str(output_dir / "poster.png")
    scene.render.image_settings.file_format = "PNG"
    bpy.ops.render.render(write_still=True)

    frames_dir = output_dir / ".frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    scene.frame_set(scene.frame_start)
    scene.render.filepath = str(frames_dir / "frame_")
    scene.render.image_settings.file_format = "PNG"
    bpy.ops.render.render(animation=True)


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    spec = json.loads(args.scene.read_text(encoding="utf-8"))
    reset_scene()
    add_lighting()
    objects = {entity["id"]: add_entity(entity, int(spec["fps"])) for entity in spec["entities"]}
    camera = add_camera(spec["camera"], objects, int(spec["fps"]))
    bpy.context.scene.camera = camera
    configure_scene(spec, args.output_dir)
    bpy.ops.wm.save_as_mainfile(filepath=str(args.output_dir / "scene.blend"))
    bpy.ops.export_scene.gltf(filepath=str(args.output_dir / "scene.glb"), export_format="GLB")
    render_artifacts(spec, args.output_dir)
    bpy.ops.wm.save_as_mainfile(filepath=str(args.output_dir / "scene.blend"))


if __name__ == "__main__":
    main()
