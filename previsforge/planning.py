"""Provider-neutral natural-language planning through OpenAI-compatible APIs."""

from __future__ import annotations

import json
from urllib import error, request

from .model import SceneSpec, SceneSpecError
from .validation import validate_scene


class PlanningError(RuntimeError):
    """Raised when an LLM endpoint cannot produce a usable SceneSpec."""


SYSTEM_PROMPT = """You are the planning stage of PrevisForge, a local 3D whitebox previsualization system.
Return one JSON object and no commentary. It must be a SceneSpec version 1.0 with these top-level fields:
version, title, duration_seconds, fps, resolution, world_color, entities, camera, markers, metadata.
Entity kinds: box, sphere, cylinder, torus, plane, actor, empty. Every entity needs id, name, kind,
dimensions [x,y,z], color [r,g,b,a], location, rotation in degrees, scale, keyframes, metadata.
Keyframes use seconds and may contain location, rotation, scale, or focal_length. Camera needs id,
location, rotation, focal_length, optional target entity id, and keyframes. Use meters, stable IDs,
simple primitives, and strictly increasing keyframe times inside the scene duration. Prefer a clear,
editable blockout over decorative detail. Include story-beat markers and at least one animated subject.
"""


def _decode_content(content: str) -> dict[str, object]:
    text = content.strip()
    if text.startswith("```"):
        first_newline = text.find("\n")
        text = text[first_newline + 1 :] if first_newline >= 0 else text
        if text.endswith("```"):
            text = text[:-3]
    try:
        result = json.loads(text.strip())
    except json.JSONDecodeError as error:
        raise PlanningError(f"Planner returned invalid JSON: {error}") from error
    if not isinstance(result, dict):
        raise PlanningError("Planner response must be a JSON object")
    return result


def plan_scene(
    prompt: str,
    *,
    endpoint: str,
    model: str,
    api_key: str | None = None,
    timeout: float = 120,
) -> SceneSpec:
    if not prompt.strip():
        raise PlanningError("Prompt cannot be empty")
    url = endpoint.rstrip("/") + "/chat/completions"
    body = json.dumps(
        {
            "model": model,
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        }
    ).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    http_request = request.Request(url, data=body, headers=headers, method="POST")
    try:
        with request.urlopen(http_request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
        content = payload["choices"][0]["message"]["content"]
        scene = SceneSpec.from_dict(_decode_content(content))
    except (error.URLError, TimeoutError, KeyError, IndexError, TypeError, json.JSONDecodeError, SceneSpecError) as exc:
        raise PlanningError(f"Planner request failed: {exc}") from exc
    report = validate_scene(scene)
    if not report.valid:
        codes = ", ".join(finding.code for finding in report.errors)
        raise PlanningError(f"Planner returned an invalid SceneSpec: {codes}")
    return scene
