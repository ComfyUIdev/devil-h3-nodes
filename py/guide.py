"""Draw the placement sheet with numpy. No image files are read.

The sheet is warm paper, near-black frames, warm-gray line figures, and small
devil-red joint dots. The prompt tells H3 to treat the ink as placement only.
"""

from __future__ import annotations

import numpy as np

from .figures import plan_for

PAPER = (247, 244, 239)
INK = (90, 80, 76)
FRAME = (26, 16, 14)
JOINT = (226, 91, 69)


def _stamp(image, x, y, color, radius):
    height, width = image.shape[:2]
    x0 = max(0, x - radius)
    x1 = min(width, x + radius + 1)
    y0 = max(0, y - radius)
    y1 = min(height, y + radius + 1)
    if x1 > x0 and y1 > y0:
        image[y0:y1, x0:x1] = color


def _line(image, x0, y0, x1, y1, color, radius):
    steps = max(abs(x1 - x0), abs(y1 - y0), 1)
    for step in range(steps + 1):
        x = x0 + (x1 - x0) * step // steps
        y = y0 + (y1 - y0) * step // steps
        _stamp(image, x, y, color, radius)


def _rect(image, x, y, w, h, color, radius, filled):
    if w <= 0 or h <= 0:
        return
    if filled:
        height, width = image.shape[:2]
        x0 = max(0, min(width, x))
        y0 = max(0, min(height, y))
        x1 = max(0, min(width, x + w))
        y1 = max(0, min(height, y + h))
        if x1 > x0 and y1 > y0:
            image[y0:y1, x0:x1] = color
        return
    _line(image, x, y, x + w, y, color, radius)
    _line(image, x, y + h, x + w, y + h, color, radius)
    _line(image, x, y, x, y + h, color, radius)
    _line(image, x + w, y, x + w, y + h, color, radius)


def _oval(image, cx, cy, rx, ry, color, thick):
    if rx < 1 or ry < 1:
        return
    height, width = image.shape[:2]
    y0 = max(0, cy - ry - thick)
    y1 = min(height, cy + ry + thick + 1)
    x0 = max(0, cx - rx - thick)
    x1 = min(width, cx + rx + thick + 1)
    if y1 <= y0 or x1 <= x0:
        return
    grid_y, grid_x = np.ogrid[y0:y1, x0:x1]
    nx = (grid_x - cx) / rx
    ny = (grid_y - cy) / ry
    dist = np.sqrt(nx * nx + ny * ny)
    band = thick / float(min(rx, ry))
    mask = (dist <= 1.0 + band) & (dist >= 1.0 - band)
    image[y0:y1, x0:x1][mask] = color


def _map(box, value, horizontal):
    left, top, right, bottom = box
    span = (right - left) if horizontal else (bottom - top)
    origin = left if horizontal else top
    return origin + value * span // 1000


def _draw_plan(image, box, view_id):
    left, top, right, bottom = box
    span = min(right - left, bottom - top)
    radius = max(1, span // 180)
    for op in plan_for(view_id):
        kind = op[0]
        if kind == "line":
            x0, y0 = _map(box, op[1], True), _map(box, op[2], False)
            x1, y1 = _map(box, op[3], True), _map(box, op[4], False)
            _line(image, x0, y0, x1, y1, INK, radius)
        elif kind == "rect":
            x = _map(box, op[1], True)
            y = _map(box, op[2], False)
            w = max(1, op[3] * (right - left) // 1000)
            h = max(1, op[4] * (bottom - top) // 1000)
            _rect(image, x, y, w, h, INK, radius, False)
        elif kind == "fill":
            x = _map(box, op[1], True)
            y = _map(box, op[2], False)
            w = max(1, op[3] * (right - left) // 1000)
            h = max(1, op[4] * (bottom - top) // 1000)
            _rect(image, x, y, w, h, INK, radius, True)
        elif kind == "oval":
            cx, cy = _map(box, op[1], True), _map(box, op[2], False)
            rx = max(2, op[3] * (right - left) // 1000)
            ry = max(2, op[4] * (bottom - top) // 1000)
            _oval(image, cx, cy, rx, ry, INK, max(1, radius))
        elif kind == "dot":
            cx, cy = _map(box, op[1], True), _map(box, op[2], False)
            _stamp(image, cx, cy, JOINT, max(2, span // 70))


def render_guide(layout: dict) -> bytes:
    """Return packed RGB bytes, row-major, one byte per channel."""
    width = int(layout["width"])
    height = int(layout["height"])
    image = np.empty((height, width, 3), dtype=np.uint8)
    image[:] = PAPER
    frame = max(2, min(width, height) // 180)
    for panel in layout["panels"]:
        left = int(round(panel["rect"][0] * width))
        top = int(round(panel["rect"][1] * height))
        right = int(round((panel["rect"][0] + panel["rect"][2]) * width))
        bottom = int(round((panel["rect"][1] + panel["rect"][3]) * height))
        left = max(0, min(width - 2, left))
        top = max(0, min(height - 2, top))
        right = max(left + 2, min(width, right))
        bottom = max(top + 2, min(height, bottom))
        _rect(image, left, top, right - left, bottom - top, FRAME, frame, False)
        inset = frame + 4
        inner = [left + inset, top + inset, right - inset, bottom - inset]
        if inner[2] - inner[0] > 8 and inner[3] - inner[1] > 8:
            _draw_plan(image, inner, panel["id"])
    return image.tobytes()
