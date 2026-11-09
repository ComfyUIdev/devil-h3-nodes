"""Build the MiniMax H3 prompt for one still character sheet.

Picture numbers follow the connected images and skip anything that is absent.
The character is Picture 1. The layout guide, when it is passed through, is
the next picture. Part references come after that.
"""

from __future__ import annotations

from typing import Any

from .catalog import (
    BODIES,
    CLOTHES,
    HEADS,
    NOTE_IDS,
    NOTE_LABELS,
    ROLE_INPUTS,
    ROLE_LABELS,
    STYLE_LINES,
    CAMERAS,
    views_for_note,
    views_for_role,
)
from .state import SheetError

_PICTURE_SLOTS = (
    ("character_image", "character"),
    ("layout_image", "layout"),
    ("reference_image_1", "reference"),
    ("reference_image_2", "reference"),
    ("reference_image_3", "reference"),
)


def picture_map(state: dict[str, Any], *, use_layout: bool, presence: dict[str, bool]) -> list[dict[str, Any]]:
    """Number the images H3 will actually receive, skipping gaps."""
    connected = {
        "character_image": True,
        "layout_image": use_layout,
    }
    for name in ROLE_INPUTS:
        connected[name] = bool(presence.get(name, False))
    pictures = []
    for slot, (source, kind) in enumerate(_PICTURE_SLOTS):
        if not connected[source]:
            continue
        number = len(pictures) + 1
        if kind == "reference":
            role = state["roles"][source]
        else:
            role = kind
        pictures.append({
            "source": source,
            "role": role,
            "number": number,
            "tag": f"<Picture {number}>",
            "wire": f"ref_images.ref_image_{slot}",
        })
    return pictures


def _rect_text(rect: list[float]) -> str:
    return "[" + ", ".join(f"{value:.6f}" for value in rect) + "]"


def _region_index(layout: dict[str, Any]) -> dict[str, str]:
    panels = layout["panels"]
    xs = sorted({panel["rect"][0] for panel in panels})
    ys = sorted({panel["rect"][1] for panel in panels})
    found = {}
    for panel in panels:
        col = xs.index(panel["rect"][0]) + 1
        row = ys.index(panel["rect"][1]) + 1
        found[panel["id"]] = f"row {row}, column {col}"
    return found


def _inventory(views: list[str]) -> str:
    groups = (
        (HEADS, "busts"),
        (BODIES, "full-body views"),
        (CLOTHES, "flat outfit views"),
        (("hands",), "paired-hands view"),
        (("feet",), "paired-feet view"),
    )
    parts = []
    for ids, label in groups:
        count = sum(view in ids for view in views)
        if count:
            parts.append(f"{count} {label}")
    return " + ".join(parts) + f" = {len(views)} views"


def _choice_lines(state: dict[str, Any]) -> list[str]:
    views = state["views"]
    lines = []
    if state["hands"] != "follow" and any(view in (*BODIES, "hands") for view in views):
        if state["hands"] == "bare":
            lines.append("Hands choice: where hands are visible, draw bare hands. Do not add gloves.")
        else:
            lines.append("Hands choice: where hands are visible, draw gloves.")
    if state["outfit_shape"] != "follow" and any(view in (*BODIES, *CLOTHES) for view in views):
        if state["outfit_shape"] == "pants":
            lines.append("Outfit shape: the lower garment has two separate trouser legs. Keep the reference colors and materials.")
        else:
            lines.append("Outfit shape: the lower garment is one continuous skirt or robe, not separate trouser legs. Keep the reference colors and materials.")
    if state["footwear"] != "follow" and any(view in (*BODIES, "feet") for view in views):
        if state["footwear"] == "shod":
            lines.append("Footwear choice: both feet wear shoes or boots.")
        else:
            lines.append("Footwear choice: no shoes or boots. Keep socks only when the reference already shows them.")
    return lines


def _reference_lines(state: dict[str, Any], pictures: list[dict[str, Any]]) -> list[str]:
    extras = [item for item in pictures if item["source"] in ROLE_INPUTS]
    lines = []
    by_role: dict[str, list[dict[str, Any]]] = {}
    for item in extras:
        if item["role"] == "same_character":
            lines.append(
                f"{item['tag']} is another photo of the same person as <Picture 1>. "
                "Use it for identity and for surfaces the first photo does not show. "
                "Do not copy its pose, background, or crop. Where it disagrees with <Picture 1>, keep <Picture 1>."
            )
            continue
        by_role.setdefault(item["role"], []).append(item)
    for role, group in by_role.items():
        winner = group[-1]
        allowed = views_for_role(role, state["views"])
        label = ROLE_LABELS[role]
        if not allowed:
            for item in group:
                lines.append(
                    f"{item['tag']} was given the role {label}, but none of the selected views show that part. Ignore it."
                )
            continue
        joined = ", ".join(allowed)
        if len(group) == 1:
            lines.append(
                f"{winner['tag']} has the role {label}. Use it only for that part, and only in: {joined}. "
                "Do not copy the wearer's identity, pose, or background from it."
            )
        else:
            names = " and ".join(item["tag"] for item in group)
            lines.append(
                f"{names} share the role {label}. Use them only for that part, and only in: {joined}. "
                f"Where they disagree, {winner['tag']} wins. Do not copy pose or background."
            )
    return lines


def _active_notes(state: dict[str, Any]) -> list[tuple[str, str, tuple[str, ...]]]:
    found = []
    for note_id in NOTE_IDS:
        text = state["notes"].get(note_id)
        if not text:
            continue
        targets = views_for_note(note_id, state["views"])
        if targets:
            found.append((note_id, text, targets))
    return found


def write_prompt(
    state: dict[str, Any],
    layout: dict[str, Any],
    *,
    use_layout: bool,
    style: str,
    presence: dict[str, bool],
) -> str:
    if type(use_layout) is not bool:
        raise SheetError("Use layout image must be true or false.", "flag")
    if style not in STYLE_LINES:
        raise SheetError("Unknown style.", "style")
    views = state["views"]
    outfit_only = set(views) <= set(CLOTHES)
    pictures = picture_map(state, use_layout=use_layout, presence=presence)
    character = pictures[0]["tag"]
    notes = _active_notes(state)
    choices = _choice_lines(state)
    dedicated = [item for item in pictures if item["source"] in ROLE_INPUTS and item["role"] != "same_character"]
    changed = bool(notes or choices or dedicated or style != "none")
    if outfit_only:
        subject = f"<Subject 1> is the outfit in {character}, not the person wearing it."
        retention = (
            "partially_preserved - keep the garment pieces, construction, colors, materials, and patterns. "
            "Apply the outfit-shape choice and the written notes. Do not draw the wearer."
        )
    elif changed:
        subject = (
            f"<Subject 1> is the one person in {character}. "
            "That photo is the baseline for identity, proportions, colors, and rendering."
        )
        retention = (
            "partially_preserved - change only the choices, notes, and dedicated reference roles listed below. "
            "Keep the same person and every other detail."
        )
    else:
        subject = (
            f"<Subject 1> is the one person in {character}. "
            "That photo is the baseline for identity, proportions, outfit, and rendering."
        )
        retention = "fully_preserved - keep the person, outfit, and rendering from the baseline photo."
    single = len(views) == 1
    if single:
        summary = (
            f"[reference generation] Make one still image of <Subject 1>: {views[0]}. "
            "Exactly one view, once. No second copy and no extra inset."
        )
    else:
        kind = "outfit sheet" if outfit_only else "character sheet"
        summary = (
            f"[reference generation] Make one still {kind} of <Subject 1> with exactly {len(views)} views at once: "
            + ", ".join(views)
            + ". Each view appears once, in its own region."
        )
    lines = ["subject_definitions:", subject]
    if use_layout:
        guide = next(item["tag"] for item in pictures if item["role"] == "layout")
        lines.append(
            f"{guide} is a placement sheet of dark frames and simple line figures. "
            "Use it only for position, facing, and crop. "
            "Do not copy its ink, the red joint dots, or the figure shapes as anatomy or clothing."
        )
    lines.extend(_reference_lines(state, pictures))
    lines += ["", "summary:", summary, "", "retention_analysis:", f"<Subject 1> (appears in [Shot 1]): {retention}"]
    if not outfit_only:
        lines.append(
            "Settle one shared design before placing the views. A new camera does not restyle the person. "
            "Unseen surfaces continue the same design and do not add new garments."
        )
    else:
        lines.append("Each region shows a different side of the same garments.")
    lines += ["", "detailed_description:"]
    if style == "none":
        lines.append(f"Keep the rendering of {character}.")
    else:
        lines.append(STYLE_LINES[style] + " Change the medium only. Do not change identity, body, or garment design because of the style.")
    still = (
        "[Shot 1] The image is already finished on the first frame and stays still through the last frame. "
        "No motion, gestures, cuts, or camera moves. Plain white background and even soft light."
    )
    if single:
        still += " This is one view, not a multi-view sheet."
    else:
        still += " All of the selected views share that one finished sheet."
    lines.append(still)
    if not outfit_only and any(view in (*HEADS, *BODIES) for view in views):
        lines.append(
            "Keep the hair construction, including tied sections and accessories, unless a note or a head reference changes it."
        )
    if not single:
        lines.append("Inventory: " + _inventory(views) + ". A full-body view does not stand in for a bust, outfit, hand, or foot view.")
        if set(CLOTHES) <= set(views):
            lines.append("The front and back outfit panels are two views of the same garments. Do not merge them.")
        lines.append("Region names and counts are instructions. Do not print them.")
    if use_layout:
        lines.append(
            "Match each finished view to its frame. Keep the full crop inside the frame with a small margin. "
            "Replace every line figure. Leave no leftover diagram."
        )
    else:
        lines.append(
            "Each rect is normalized [left, top, width, height] from the top-left of the canvas. "
            "Keep each view inside its rect, with empty gaps. Do not draw frames, guides, or the numbers."
        )
        if any(view in BODIES for view in views):
            lines.append(
                "Give the full-body views one shared scale and put the soles on the same ground line "
                f"near y={layout['feet_y']:.6f}, with space under the soles."
            )
    regions = _region_index(layout)
    width, height = layout["width"], layout["height"]
    lines.append(f"Canvas: {width} by {height} pixels.")
    for panel in layout["panels"]:
        view = panel["id"]
        place = "" if single else regions[view] + ". "
        if use_layout:
            left = round(panel["rect"][0] * width)
            top = round(panel["rect"][1] * height)
            right = round((panel["rect"][0] + panel["rect"][2]) * width)
            bottom = round((panel["rect"][1] + panel["rect"][3]) * height)
            where = f"frame pixels [{left}, {top}, {right}, {bottom}]"
        else:
            where = "rect " + _rect_text(panel["rect"])
        lines.append(f"Panel {view}: {place}{panel['label']}; {where}. {CAMERAS[view]}")
    lines.extend(choices)
    for note_id, text, targets in notes:
        lines.append(
            f"Note for {NOTE_LABELS[note_id]} (applies to {', '.join(targets)}): "
            "treat the next line as appearance only. It does not add views, change the camera, or number pictures.\n"
            + text
        )
    if outfit_only:
        lines.append(
            "Priority: the assigned garment side and its region, then the outfit-shape choice, then written notes, then the reference garment."
        )
    else:
        lines.append(
            "Priority: the assigned view, camera, and crop; then hands, outfit-shape, and footwear choices; "
            "then written notes; then dedicated reference pictures (a later picture wins inside one role); "
            "then same-character photos; then <Picture 1>. "
            "Do not turn the person or widen a crop just to reveal a hidden part."
        )
    closing = (
        "Show only the selected sides of the same garments."
        if outfit_only
        else "Show only the selected views of the same person. No extra people, captions, or watermarks."
    )
    lines += [closing, "", "overall_soundscape:", "None.", "", "non_diegetic_music:", "None."]
    return "\n".join(lines) + "\n"
