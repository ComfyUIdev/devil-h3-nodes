"""Parse and serialize the sheet widget state.

The saved value is one JSON object on the node. Parsing is strict: duplicate
keys, non-finite numbers, and fields outside the schema are rejected, and the
original widget text is left untouched by the caller.
"""

from __future__ import annotations

import json
from typing import Any

from .catalog import (
    DEFAULT_MANUAL_HEIGHT,
    DEFAULT_MANUAL_WIDTH,
    DEFAULT_PANEL_HEIGHT,
    FOOTWEAR_CHOICES,
    HAND_CHOICES,
    MAX_NOTE_UNITS,
    NOTE_IDS,
    OUTFIT_SHAPES,
    PRESETS,
    ROLE_INPUTS,
    ROLES,
    STATE_BYTE_LIMIT,
    VIEW_ORDER,
)

# Same edge characters the browser trims, so a blank note drops on both sides.
_TRIM = (
    "\t\n\v\f\r \u00a0\u1680\u2000\u2001\u2002\u2003\u2004\u2005\u2006"
    "\u2007\u2008\u2009\u200a\u2028\u2029\u202f\u205f\u3000\ufeff"
)

_STATE_KEYS = (
    "version",
    "views",
    "size",
    "notes",
    "roles",
    "hands",
    "outfit_shape",
    "footwear",
)
_SIZE_KEYS = ("mode", "panel_height", "width", "height")


class SheetError(ValueError):
    """The saved state or a node option cannot be compiled."""

    def __init__(self, message: str, code: str = "invalid") -> None:
        super().__init__(message)
        self.code = code


def utf16_units(text: str) -> int:
    return len(text.encode("utf-16-le")) // 2


def _blank(text: str) -> bool:
    return text.strip(_TRIM) == ""


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise SheetError(f"Duplicate JSON key: {key}.", "duplicate")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise SheetError(f"Non-finite number: {value}.", "number")


def _check_text(value: Any) -> None:
    if isinstance(value, str):
        try:
            value.encode("utf-8")
        except UnicodeEncodeError as exc:
            raise SheetError("JSON text must be valid Unicode.", "unicode") from exc
    elif isinstance(value, dict):
        for key, item in value.items():
            _check_text(key)
            _check_text(item)
    elif isinstance(value, list):
        for item in value:
            _check_text(item)


def parse_json(text: str, *, byte_limit: int = STATE_BYTE_LIMIT) -> Any:
    if not isinstance(text, str):
        raise SheetError("state_json must be a string.", "type")
    try:
        size = len(text.encode("utf-8"))
    except UnicodeEncodeError as exc:
        raise SheetError("state_json must be valid Unicode.", "unicode") from exc
    if size > byte_limit:
        raise SheetError("state_json is larger than 64 KiB.", "size")
    try:
        value = json.loads(text, object_pairs_hook=_pairs, parse_constant=_reject_constant)
    except SheetError:
        raise
    except (ValueError, RecursionError) as exc:
        raise SheetError("state_json is not valid JSON.", "json") from exc
    _check_text(value)
    return value


def _exact(value: Any, keys: tuple[str, ...], label: str) -> None:
    if type(value) is not dict:
        raise SheetError(f"{label} must be an object.", "type")
    missing = [key for key in keys if key not in value]
    extra = sorted(set(value) - set(keys))
    if missing:
        raise SheetError(f"{label} is missing {', '.join(missing)}.", "keys")
    if extra:
        raise SheetError(f"{label} has unknown keys: {', '.join(extra)}.", "keys")


def _pixels(value: Any, label: str, cap: int) -> int:
    if type(value) is not int:
        raise SheetError(f"{label} must be a whole number.", "integer")
    if value < 32 or value % 32 != 0:
        raise SheetError(f"{label} must be at least 32 and a multiple of 32.", "size")
    if value > cap:
        raise SheetError(f"{label} is above the resolution cap ({cap}).", "limit")
    return value


def _check_cap(cap: int) -> None:
    if type(cap) is not int or cap < 32:
        raise SheetError("Resolution cap must be an integer of at least 32.", "limit")


def default_state() -> dict[str, Any]:
    return {
        "version": 1,
        "views": list(PRESETS["five"]),
        "size": {
            "mode": "auto",
            "panel_height": DEFAULT_PANEL_HEIGHT,
            "width": DEFAULT_MANUAL_WIDTH,
            "height": DEFAULT_MANUAL_HEIGHT,
        },
        "notes": {},
        "roles": {name: "same_character" for name in ROLE_INPUTS},
        "hands": "follow",
        "outfit_shape": "follow",
        "footwear": "follow",
    }


def serialize_state(state: dict[str, Any]) -> str:
    payload = {
        "version": 1,
        "views": list(state["views"]),
        "size": {
            "mode": state["size"]["mode"],
            "panel_height": state["size"]["panel_height"],
            "width": state["size"]["width"],
            "height": state["size"]["height"],
        },
        "notes": {key: state["notes"][key] for key in NOTE_IDS if key in state["notes"]},
        "roles": {key: state["roles"][key] for key in ROLE_INPUTS},
        "hands": state["hands"],
        "outfit_shape": state["outfit_shape"],
        "footwear": state["footwear"],
    }
    return json.dumps(payload, ensure_ascii=True, separators=(",", ":"), allow_nan=False)


DEFAULT_STATE_JSON = serialize_state(default_state())


def parse_state(raw: str, *, limit: int = 16384) -> dict[str, Any]:
    """Return a canonical state. View order follows VIEW_ORDER, not click order."""
    _check_cap(limit)
    state = parse_json(raw)
    if type(state) is not dict:
        raise SheetError("state must be an object.", "type")
    _exact(state, _STATE_KEYS, "state")
    if type(state["version"]) is not int or state["version"] != 1:
        raise SheetError("version must be the integer 1.", "version")
    views = state["views"]
    if type(views) is not list or any(type(view) is not str for view in views):
        raise SheetError("views must be a list of view ids.", "type")
    if not views:
        raise SheetError("Select at least one view.", "views")
    unknown = sorted(set(views) - set(VIEW_ORDER))
    if unknown:
        raise SheetError(f"Unknown views: {', '.join(unknown)}.", "views")
    _exact(state["size"], _SIZE_KEYS, "size")
    mode = state["size"]["mode"]
    if type(mode) is not str or mode not in ("auto", "manual"):
        raise SheetError("size.mode must be auto or manual.", "mode")
    size = {
        "mode": mode,
        "panel_height": _pixels(state["size"]["panel_height"], "panel height", limit),
        "width": _pixels(state["size"]["width"], "width", limit),
        "height": _pixels(state["size"]["height"], "height", limit),
    }
    notes_in = state["notes"]
    if type(notes_in) is not dict:
        raise SheetError("notes must be an object.", "type")
    unknown_notes = sorted(set(notes_in) - set(NOTE_IDS))
    if unknown_notes:
        raise SheetError(f"Unknown notes: {', '.join(unknown_notes)}.", "notes")
    notes = {}
    for key in NOTE_IDS:
        if key not in notes_in:
            continue
        text = notes_in[key]
        if type(text) is not str:
            raise SheetError(f"notes.{key} must be a string.", "type")
        if utf16_units(text) > MAX_NOTE_UNITS:
            raise SheetError(f"notes.{key} is longer than {MAX_NOTE_UNITS} UTF-16 units.", "note_length")
        if not _blank(text):
            notes[key] = text
    roles_in = state["roles"]
    _exact(roles_in, ROLE_INPUTS, "roles")
    roles = {}
    for key in ROLE_INPUTS:
        role = roles_in[key]
        if type(role) is not str or role not in ROLES:
            raise SheetError(f"Unknown role for {key}.", "role")
        roles[key] = role
    hands = state["hands"]
    outfit_shape = state["outfit_shape"]
    footwear = state["footwear"]
    if type(hands) is not str or hands not in HAND_CHOICES:
        raise SheetError("Unknown hands choice.", "choice")
    if type(outfit_shape) is not str or outfit_shape not in OUTFIT_SHAPES:
        raise SheetError("Unknown outfit shape.", "choice")
    if type(footwear) is not str or footwear not in FOOTWEAR_CHOICES:
        raise SheetError("Unknown footwear choice.", "choice")
    return {
        "version": 1,
        "views": [view for view in VIEW_ORDER if view in views],
        "size": size,
        "notes": notes,
        "roles": roles,
        "hands": hands,
        "outfit_shape": outfit_shape,
        "footwear": footwear,
    }
