#!/usr/bin/env python3
"""Spritesheet Normalizer — re-execs into the Friday SDK Python if needed."""

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

from friday_agent_sdk import agent, ok, err, run, AgentContext

IMAGE_PROCESSOR_SCRIPT = r"""
import json, math, sys, os
from PIL import Image
from collections import Counter

NEON_GREEN = (0, 255, 0)
NEON_GREEN_TOLERANCE = 30


def detect_background(img, sample_size=3):
    w, h = img.size
    pixels = []
    corners = [
        (0, 0), (w - sample_size, 0),
        (0, h - sample_size), (w - sample_size, h - sample_size)
    ]
    for cx, cy in corners:
        for dx in range(sample_size):
            for dy in range(sample_size):
                px = img.getpixel((
                    min(max(cx + dx, 0), w - 1),
                    min(max(cy + dy, 0), h - 1)
                ))
                pixels.append(px[:3])
    return Counter(pixels).most_common(1)[0][0]


def color_distance(c1, c2):
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(c1, c2)))


def is_bg_color(rgb, bg, threshold=NEON_GREEN_TOLERANCE):
    return rgb == NEON_GREEN or color_distance(rgb, bg) <= threshold


def make_transparent(frame, bg, threshold=30):
    data = frame.load()
    w, h = frame.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = data[x, y]
            rgb = (r, g, b)
            if rgb == NEON_GREEN or color_distance(rgb, bg) <= threshold:
                data[x, y] = (r, g, b, 0)
    return frame


def find_frame_boundaries(img, frame_count, bg, threshold=NEON_GREEN_TOLERANCE):
    # Detect actual frame boundaries by scanning for full-height background columns.
    # Returns list of (x_start, x_end) tuples or None if detection fails.
    # A column is a separator when >= 95% of its pixels match the background.
    w, h = img.size
    pixels = img.load()

    def col_is_bg(x):
        bg_count = sum(
            1 for y in range(h)
            if is_bg_color(pixels[x, y][:3], bg, threshold)
        )
        return bg_count / h >= 0.95

    # Collect separator column ranges
    in_sep = False
    sep_regions = []
    sep_start = None
    for x in range(w):
        if col_is_bg(x):
            if not in_sep:
                in_sep = True
                sep_start = x
        else:
            if in_sep:
                sep_regions.append((sep_start, x - 1))
                in_sep = False
    if in_sep:
        sep_regions.append((sep_start, w - 1))

    # Build content spans between separator regions
    content_spans = []
    prev_end = 0
    for s_start, s_end in sep_regions:
        if s_start > prev_end:
            content_spans.append((prev_end, s_start))
        prev_end = s_end + 1
    if prev_end < w:
        content_spans.append((prev_end, w))

    if len(content_spans) == frame_count:
        return content_spans

    return None


def process(params):
    image_path = params["image_path"]
    frame_count = int(params["frame_count"])
    frame_w = int(params["frame_w"])
    frame_h = int(params["frame_h"])
    output_path = params["output_path"]

    img = Image.open(image_path).convert("RGBA")
    bg = detect_background(img)

    expected_w = frame_w * frame_count
    actual_w = img.width
    dimension_mismatch = actual_w != expected_w

    boundaries = None
    detection_method = "even-split"

    if dimension_mismatch:
        boundaries = find_frame_boundaries(img, frame_count, bg)
        if boundaries:
            detection_method = "boundary-detected"
        else:
            return {
                "ok": False,
                "regenerate": True,
                "error": (
                    f"Canvas is {actual_w}x{img.height} but expected {expected_w}x{frame_h} "
                    f"({frame_count} frames x {frame_w}px). Boundary detection found no clean "
                    f"separators — image likely contains doubled or malformed frames. "
                    f"Regeneration required."
                ),
            }

    canvas = Image.new("RGBA", (frame_count * frame_w, frame_h), (0, 0, 0, 0))

    for i in range(frame_count):
        if boundaries:
            x0, x1 = boundaries[i]
        else:
            x0 = i * (actual_w // frame_count)
            x1 = x0 + (actual_w // frame_count)

        frame = img.crop((x0, 0, x1, img.height))
        frame = frame.resize((frame_w, frame_h), Image.NEAREST)
        frame = make_transparent(frame, bg)
        canvas.paste(frame, (i * frame_w, 0), frame)

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    canvas.save(output_path, "PNG", optimize=False)

    return {
        "ok": True,
        "data": {
            "output_path": output_path,
            "frame_count": frame_count,
            "frame_size": f"{frame_w}x{frame_h}",
            "background_color_detected": f"rgb({bg[0]},{bg[1]},{bg[2]})",
            "input_dimensions": f"{img.width}x{img.height}",
            "detection_method": detection_method,
            "dimension_mismatch": dimension_mismatch,
        },
    }

with open(sys.argv[1]) as f:
    params = json.load(f)
try:
    result = process(params)
    print(json.dumps(result))
except Exception as e:
    import traceback
    print(json.dumps({"ok": False, "error": str(e), "traceback": traceback.format_exc()}))
"""


def _find_destination_path(prompt: str) -> str | None:
    m = re.search(r"destination_path:\s*(/[^\s;,\n\"']+\.png)", prompt)
    if m:
        return m.group(1)
    return None


def _parse_frame_params(prompt: str) -> dict:
    defaults = {"frame_count": 4, "frame_w": 64, "frame_h": 64}
    try:
        for m in re.finditer(r'\{[^{}]+\}', prompt):
            try:
                data = json.loads(m.group())
                if "frame_count" in data or "frame_w" in data:
                    return {
                        "frame_count": int(data.get("frame_count", defaults["frame_count"])),
                        "frame_w":     int(data.get("frame_w",     defaults["frame_w"])),
                        "frame_h":     int(data.get("frame_h",     defaults["frame_h"])),
                    }
            except (json.JSONDecodeError, ValueError):
                continue
    except Exception:
        pass

    result = {}
    for key, pat, default in [
        ("frame_count", r'"?frame_count"?\s*[=:]\s*(\d+)', 4),
        ("frame_w",     r'"?frame_w"?\s*[=:]\s*(\d+)',     64),
        ("frame_h",     r'"?frame_h"?\s*[=:]\s*(\d+)',     64),
    ]:
        m = re.search(pat, prompt)
        result[key] = int(m.group(1)) if m else default
    return result


@agent(
    id="spritesheet-normalizer",
    version="1.1.0",
    description=(
        "Normalizes a raw AI-generated spritesheet PNG/JPEG into a clean RGBA PNG "
        "with exact frame dimensions, transparent background (detected from image corners), "
        "and NEAREST-resampled pixel art frames. "
        "When canvas dimensions do not match expected (frame_count x frame_w), attempts "
        "neon-green column boundary detection to find actual frame edges. "
        "If boundary detection also fails, returns regenerate=True so the FSM can re-trigger generation."
    ),
)
def spritesheet_normalizer(prompt: str, ctx: AgentContext):
    image_path = _find_destination_path(prompt)
    if not image_path:
        return err(f"Could not find destination_path in prompt. Prompt starts: {prompt[:300]}")

    if not os.path.isfile(image_path):
        return err(f"Image file not found: {image_path}")

    params = _parse_frame_params(prompt)
    output_path = image_path  # normalize in-place

    run_params = {
        "image_path": image_path,
        "frame_count": params["frame_count"],
        "frame_w": params["frame_w"],
        "frame_h": params["frame_h"],
        "output_path": output_path,
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as sf:
        sf.write(IMAGE_PROCESSOR_SCRIPT)
        script_path = sf.name

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as pf:
        json.dump(run_params, pf)
        params_path = pf.name

    try:
        result = subprocess.run(
            [_FRIDAY_PYTHON, script_path, params_path],
            capture_output=True, text=True, timeout=120,
        )
    except subprocess.TimeoutExpired:
        return err("Image processing timed out after 120s")
    finally:
        os.unlink(script_path)
        os.unlink(params_path)

    if result.returncode != 0:
        return err(f"Processing failed (exit {result.returncode}): {result.stderr.strip()}")

    stdout = result.stdout.strip()
    if not stdout:
        return err(f"Processor produced no output. stderr: {result.stderr.strip()}")

    try:
        output = json.loads(stdout)
    except json.JSONDecodeError:
        return err(f"Unexpected output: {stdout[:500]}")

    if not output.get("ok"):
        # Surface regenerate flag so FSM can branch on it
        return ok({
            "regenerate": output.get("regenerate", False),
            "error": output.get("error", "Unknown error"),
        })

    return ok(output["data"])


if __name__ == "__main__":
    run()
