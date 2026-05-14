#!/usr/bin/env python3
"""File Saver — fetches an artifact from the Friday API and saves it to disk as PNG."""

import os
import sys

_FRIDAY_PYTHON = "~/.friday/local/uv/cache/environments-v2/454d67ca501fd545/7d6b432fb870bfee/bin/python3.12"

try:
    import friday_agent_sdk  # noqa: F401
except ImportError:
    os.execv(_FRIDAY_PYTHON, [_FRIDAY_PYTHON] + sys.argv)

import json
import re
import subprocess
import tempfile
from datetime import datetime, timezone

from friday_agent_sdk import agent, ok, err, run, AgentContext


def _parse_output_dir(prompt: str) -> str:
    m = re.search(r"[Oo]utput directory[:\s]+(/[^\n.{]+)", prompt)
    if m:
        return m.group(1).strip().rstrip(".")
    return "~/game_assets"


def _parse_prefix(prompt: str) -> str:
    """Extract filename prefix, e.g. 'spritesheet_' or 'asset_'."""
    m = re.search(r"prefix[:\s]+['\"]?([a-z_]+)['\"]?", prompt, re.IGNORECASE)
    if m:
        return m.group(1).strip("_") + "_"
    return "asset_"


def _find_artifact_id(ctx: AgentContext, prompt: str) -> str | None:
    def find_in(obj, depth=0):
        if depth > 6 or not obj:
            return None
        if isinstance(obj, list):
            for item in obj:
                r = find_in(item, depth + 1)
                if r:
                    return r
        elif isinstance(obj, dict):
            refs = obj.get("artifactRefs", [])
            if refs and isinstance(refs, list):
                for ref in refs:
                    if isinstance(ref, dict) and ref.get("id"):
                        return ref["id"]
            for v in obj.values():
                r = find_in(v, depth + 1)
                if r:
                    return r
        return None

    if hasattr(ctx, "input") and ctx.input:
        result = find_in(ctx.input)
        if result:
            return result

    for m in re.finditer(r'"artifactRefs"\s*:\s*\[.*?"id"\s*:\s*"([0-9a-f-]{36})"', prompt, re.DOTALL):
        return m.group(1)

    return None


@agent(
    id="file-saver",
    version="2.0.0",
    description=(
        "Fetches a generated image artifact from the Friday API and saves it to disk as PNG. "
        "Uses a timestamp-based filename. Returns destination_path."
    ),
)
def file_saver(prompt: str, ctx: AgentContext):
    output_dir = _parse_output_dir(prompt)
    prefix = _parse_prefix(prompt)

    artifact_id = _find_artifact_id(ctx, prompt)
    if not artifact_id:
        return err("Could not find artifact ID in ctx.input or prompt")

    # Timestamp + short artifact ID suffix — no string interpolation, always unique
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    short_id = artifact_id.split("-")[0]
    filename = f"{prefix}{ts}_{short_id}.png"
    dest_path = os.path.join(output_dir, filename)

    os.makedirs(output_dir, exist_ok=True)

    with tempfile.NamedTemporaryFile(delete=False, suffix="_raw") as tf:
        raw_path = tf.name

    try:
        dl = subprocess.run(
            ["curl", "-sf", f"http://localhost:8080/api/artifacts/{artifact_id}/content", "-o", raw_path],
            capture_output=True, text=True, timeout=30
        )
        if dl.returncode != 0:
            return err(f"curl failed (exit {dl.returncode}): {dl.stderr.strip()}")

        if os.path.getsize(raw_path) == 0:
            return err(f"Downloaded artifact is empty (id={artifact_id})")

        # Unwrap JSON AgentResult if needed
        with open(raw_path, "rb") as f:
            first_byte = f.read(1)
        if first_byte == b"{":
            with open(raw_path) as f:
                try:
                    wrapped = json.load(f)
                    nested_refs = wrapped.get("artifactRefs", [])
                    if nested_refs:
                        nested_id = nested_refs[0].get("id")
                        dl2 = subprocess.run(
                            ["curl", "-sf", f"http://localhost:8080/api/artifacts/{nested_id}/content", "-o", raw_path],
                            capture_output=True, text=True, timeout=30
                        )
                        if dl2.returncode != 0:
                            return err(f"curl (nested) failed: {dl2.stderr.strip()}")
                        artifact_id = nested_id
                except json.JSONDecodeError:
                    pass

        conv = subprocess.run(
            ["magick", raw_path, dest_path],
            capture_output=True, text=True, timeout=30
        )
        if conv.returncode != 0:
            return err(f"magick conversion failed: {conv.stderr.strip()}")

        final_size = os.path.getsize(dest_path)
        if final_size == 0:
            return err(f"Output PNG is empty: {dest_path}")

    finally:
        if os.path.exists(raw_path):
            os.unlink(raw_path)

    return ok({
        "destination_path": dest_path,
        "artifact_id": artifact_id,
        "file_size_bytes": final_size,
        "status": "success",
    })


if __name__ == "__main__":
    run()
