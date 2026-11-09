"""Place the selected views on one sheet.

Auto mode keeps the requested full-body height and may grow the width so a
front-facing figure can stand that tall. Manual mode keeps the canvas the
user typed and scales the same arrangement to fit. Coordinates are normalized
from the top-left as [left, top, width, height], rounded half-up to 6 places.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Any

from .catalog import BODIES, CLOTHES, DETAILS, HEADS, LEGACY, SEVEN, VIEW_LABELS
from .state import SheetError

# Widest full-body figure (front and back) as width / height.
BODY_ASPECT = Fraction(21, 50)


def _round6(value: Fraction) -> float:
    numer = value.numerator * 1_000_000
    denom = value.denominator
    rounded = (2 * numer + denom) // (2 * denom)
    return rounded / 1_000_000 if rounded else 0.0


def _ceil32(value: Fraction) -> int:
    step = 32 * value.denominator
    return ((value.numerator + step - 1) // step) * 32


def _half_up(value: Fraction) -> int:
    return (2 * value.numerator + value.denominator) // (2 * value.denominator)


def _ideal(views: list[str], panel_height: int) -> tuple[dict[str, tuple[Fraction, Fraction, Fraction, Fraction]], Fraction, Fraction]:
    height = Fraction(panel_height)
    pad = height / 18
    gap = height / 30
    body_w = height * 2 / 5
    aux_w = height / 2
    selected = set(views)
    legacy = selected <= set(LEGACY) and selected != set(SEVEN)
    boxes: dict[str, tuple[Fraction, Fraction, Fraction, Fraction]] = {}
    x = pad
    y = pad
    if legacy:
        portraits = [view for view in ("face_front", "face_left") if view in selected]
        details = [view for view in DETAILS if view in selected]
        bodies = [view for view in BODIES if view in selected]
        if portraits or details:
            columns = len(portraits) if portraits else 1
            group_w = columns * aux_w + (columns - 1) * gap
            if portraits:
                portrait_h = (height * 3 / 5) if details else height
                for index, view in enumerate(portraits):
                    boxes[view] = (x + index * (aux_w + gap), y, aux_w, portrait_h)
                if details:
                    band_y = y + portrait_h + gap
                    band_h = height - portrait_h - gap
                    band_w = (group_w - gap) / 2 if len(details) == 2 else group_w
                    for index, view in enumerate(details):
                        boxes[view] = (x + index * (band_w + gap), band_y, band_w, band_h)
            elif len(details) == 2:
                band_h = (height - gap) / 2
                for index, view in enumerate(details):
                    boxes[view] = (x, y + index * (band_h + gap), aux_w, band_h)
            else:
                boxes[details[0]] = (x, y, aux_w, height)
            x += group_w + gap
        for view in bodies:
            boxes[view] = (x, y, body_w, height)
            x += body_w + gap
    else:
        portraits = [view for view in HEADS if view in selected]
        bodies = [view for view in BODIES if view in selected]
        clothes = [view for view in CLOTHES if view in selected]
        details = [view for view in DETAILS if view in selected]
        stacked_heads = selected == set(SEVEN)
        if portraits:
            cols = 1 if stacked_heads else min(2, len(portraits))
            rows = (len(portraits) + cols - 1) // cols
            cell_h = (height - (rows - 1) * gap) / rows
            for index, view in enumerate(portraits):
                col = index % cols
                row = index // cols
                boxes[view] = (x + col * (aux_w + gap), y + row * (cell_h + gap), aux_w, cell_h)
            x += cols * aux_w + (cols - 1) * gap + gap
        for view in (*bodies, *clothes):
            boxes[view] = (x, y, body_w, height)
            x += body_w + gap
        if details:
            cell_h = (height - (len(details) - 1) * gap) / len(details)
            for index, view in enumerate(details):
                boxes[view] = (x, y + index * (cell_h + gap), aux_w, cell_h)
            x += aux_w + gap
    ideal_w = x - gap + pad
    ideal_h = height + 2 * pad
    return boxes, ideal_w, ideal_h


def _pixel_boxes(boxes, scale, ox, oy, width, height):
    placed = []
    for view, (left, top, box_w, box_h) in boxes.items():
        x0 = _half_up(left * scale + ox)
        y0 = _half_up(top * scale + oy)
        x1 = _half_up((left + box_w) * scale + ox)
        y1 = _half_up((top + box_h) * scale + oy)
        x0 = max(0, min(width - 1, x0))
        y0 = max(0, min(height - 1, y0))
        x1 = max(x0 + 1, min(width, x1))
        y1 = max(y0 + 1, min(height, y1))
        placed.append({"id": view, "box": [x0, y0, x1, y1]})
    return placed


def _tighten(placed, width, height):
    """Give each panel the free space up to the midpoint of its neighbor."""
    edge = 4
    gutter = 8
    original = [item["box"][:] for item in placed]
    tightened = []
    for index, (left, top, right, bottom) in enumerate(original):
        x0, y0, x1, y1 = edge, edge, width - edge, height - edge
        for other_index, (ol, ot, oright, ob) in enumerate(original):
            if other_index == index:
                continue
            if oright <= left:
                x0 = max(x0, (oright + left) // 2 + gutter // 2)
            if ol >= right:
                x1 = min(x1, (right + ol) // 2 - gutter // 2)
            if ob <= top:
                y0 = max(y0, (ob + top) // 2 + gutter // 2)
            if ot >= bottom:
                y1 = min(y1, (bottom + ot) // 2 - gutter // 2)
        if x1 - x0 < 8 or y1 - y0 < 8:
            tightened.append([left, top, right, bottom])
        else:
            tightened.append([x0, y0, x1, y1])
    for item, box in zip(placed, tightened):
        item["box"] = box
    return placed


def _frame_px(width: int, height: int) -> int:
    return max(2, (min(width, height) + 96) // 192)


def _widen_bodies(placed, width, height, panel_height):
    bodies = [item for item in placed if item["id"] in BODIES]
    if not bodies:
        return placed, width
    frame = _frame_px(width, height)
    needed = (panel_height * BODY_ASPECT.numerator + BODY_ASPECT.denominator - 1) // BODY_ASPECT.denominator
    needed += 2 * frame + 2
    grows = []
    for item in bodies:
        left, _, right, _ = item["box"]
        grows.append(max(0, needed - (right - left)))
    extra = sum(grows)
    if extra <= 0:
        return placed, width
    new_width = ((width + extra + 31) // 32) * 32
    slack = new_width - width - extra
    share, remain = divmod(slack, len(grows))
    grows = [grow + share + (1 if index < remain else 0) for index, grow in enumerate(grows)]
    body_grow = {item["id"]: grow for item, grow in zip(bodies, grows)}
    body_edges = [(item["box"][0], item["box"][2], grow) for item, grow in zip(bodies, grows)]
    for item in placed:
        left, top, right, bottom = item["box"]
        shift = sum(grow for _, edge_r, grow in body_edges if edge_r <= left + 1)
        grow = body_grow.get(item["id"], 0)
        item["box"] = [left + shift, top, right + shift + grow, bottom]
    return placed, new_width


def _normalize(placed, width, height):
    panels = []
    for item in placed:
        left, top, right, bottom = item["box"]
        rect = [
            _round6(Fraction(left, width)),
            _round6(Fraction(top, height)),
            _round6(Fraction(right - left, width)),
            _round6(Fraction(bottom - top, height)),
        ]
        panels.append({"id": item["id"], "rect": rect, "label": VIEW_LABELS[item["id"]]})
    return panels


def plan_sheet(state: dict[str, Any], *, limit: int = 16384) -> dict[str, Any]:
    views = state["views"]
    size = state["size"]
    boxes, ideal_w, ideal_h = _ideal(views, size["panel_height"])
    if size["mode"] == "auto":
        width, height = _ceil32(ideal_w), _ceil32(ideal_h)
        scale = Fraction(1)
    else:
        width, height = size["width"], size["height"]
        scale = min(Fraction(width, 1) / ideal_w, Fraction(height, 1) / ideal_h)
    ox = (Fraction(width) - ideal_w * scale) / 2
    oy = (Fraction(height) - ideal_h * scale) / 2
    placed = _pixel_boxes(boxes, scale, ox, oy, width, height)
    # Keep canonical order even though the dict already follows it.
    order = {view: index for index, view in enumerate(views)}
    placed.sort(key=lambda item: order[item["id"]])
    placed = _tighten(placed, width, height)
    if size["mode"] == "auto":
        placed, width = _widen_bodies(placed, width, height, size["panel_height"])
    if width > limit or height > limit:
        raise SheetError(f"The sheet is above the resolution cap ({limit}).", "limit")
    panels = _normalize(placed, width, height)
    bodies = [item for item in placed if item["id"] in BODIES]
    feet_y = None if not bodies else _round6(Fraction(min(item["box"][3] for item in bodies), height))
    return {"width": width, "height": height, "panels": panels, "feet_y": feet_y}
