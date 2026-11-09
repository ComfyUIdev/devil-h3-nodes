"""ComfyUI node: Devil H3 Character Sheet.

Outputs match the native MiniMax H3 reference slots:

    prompt, width, height -> the matching H3 inputs
    character_image       -> ref_images.ref_image_0
    layout_image          -> ref_images.ref_image_1
    reference_image_1/2/3 -> ref_images.ref_image_2/3/4

Picture numbers inside the prompt skip any image that is not connected.
layout_image is None unless Use layout image is on. The four photo outputs
are the same objects that came in.
"""

from __future__ import annotations

from .catalog import DEFAULT_RESOLUTION_CAP, ROLE_INPUTS, STYLES
from .guide import render_guide
from .layout import plan_sheet
from .prompt import write_prompt
from .state import DEFAULT_STATE_JSON, SheetError, parse_state


def resolution_cap() -> int:
    """ComfyUI's cap when the host is installed, otherwise the standalone cap."""
    try:
        import nodes
    except ModuleNotFoundError:
        return DEFAULT_RESOLUTION_CAP
    cap = getattr(nodes, "MAX_RESOLUTION", None)
    if type(cap) is not int or cap < 32:
        raise SheetError("The ComfyUI resolution cap is not a usable integer.", "limit")
    return cap


def _presence_ok(presence: dict) -> None:
    if type(presence) is not dict or set(presence) - set(ROLE_INPUTS):
        raise SheetError("Reference presence is invalid.", "presence")
    if any(type(value) is not bool for value in presence.values()):
        raise SheetError("Reference presence must be true or false.", "presence")


def compile_sheet(state_json, *, use_layout=False, style="none", presence=None, limit=None):
    if type(use_layout) is not bool:
        raise SheetError("Use layout image must be true or false.", "flag")
    if type(style) is not str or style not in STYLES:
        raise SheetError("Unknown style.", "style")
    if presence is None:
        presence = {}
    _presence_ok(presence)
    cap = DEFAULT_RESOLUTION_CAP if limit is None else limit
    state = parse_state(state_json, limit=cap)
    layout = plan_sheet(state, limit=cap)
    prompt = write_prompt(state, layout, use_layout=use_layout, style=style, presence=presence)
    return {
        "state": state,
        "state_json": state_json,
        "layout": layout,
        "prompt": prompt,
        "width": layout["width"],
        "height": layout["height"],
        "use_layout": use_layout,
        "style": style,
    }


def _check_image(value, name, required):
    if value is None:
        if required:
            raise SheetError(f"Connect {name}.", "image")
        return
    shape = getattr(value, "shape", None)
    if shape is None or len(shape) != 4 or int(shape[-1]) not in (1, 3, 4):
        raise SheetError(f"{name} must be an IMAGE batch.", "image")


def pack_image(raw: bytes, width: int, height: int):
    """Wrap RGB bytes as a ComfyUI IMAGE batch. Torch is provided by ComfyUI."""
    import numpy as np
    import torch

    frame = np.frombuffer(raw, dtype=np.uint8).reshape((height, width, 3)).astype(np.float32)
    frame /= np.float32(255.0)
    copied = np.array(frame, copy=True)
    return torch.from_numpy(copied).unsqueeze(0)


class DevilH3CharacterSheet:
    CATEGORY = "Devil Nodes/H3"
    DESCRIPTION = (
        "Design a still MiniMax H3 character sheet. One character photo plus "
        "up to three part references pass through unchanged. Wire prompt, width, "
        "and height to MiniMaxH3ReferenceToVideo, character_image to ref_image_0, "
        "layout_image to ref_image_1, and reference_image_1/2/3 to ref_image_2/3/4. "
        "The layout guide is drawn either way; layout_image is empty until "
        "Use layout image is on."
    )
    SEARCH_ALIASES = [
        "h3",
        "character sheet",
        "turnaround",
        "minimax",
        "devil",
        "outfit",
    ]
    RETURN_TYPES = ("STRING", "INT", "INT", "IMAGE", "IMAGE", "IMAGE", "IMAGE", "IMAGE")
    RETURN_NAMES = (
        "prompt",
        "width",
        "height",
        "character_image",
        "layout_image",
        "reference_image_1",
        "reference_image_2",
        "reference_image_3",
    )
    FUNCTION = "build"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "state_json": (
                    "STRING",
                    {
                        "default": DEFAULT_STATE_JSON,
                        "multiline": True,
                        "dynamicPrompts": False,
                        "tooltip": "Sheet JSON: views, size, notes, and reference roles. The widget edits this.",
                    },
                ),
                "character_image": ("IMAGE", {"tooltip": "The person. Wired to H3 ref_image_0."}),
            },
            "optional": {
                "reference_image_1": ("IMAGE", {"tooltip": "Optional part reference. Wired to H3 ref_image_2."}),
                "reference_image_2": ("IMAGE", {"tooltip": "Optional part reference. Wired to H3 ref_image_3."}),
                "reference_image_3": ("IMAGE", {"tooltip": "Optional part reference. Wired to H3 ref_image_4."}),
                "use_layout_image": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": "When on, layout_image is the guide and is wired to H3 ref_image_1. When off, that output is empty. The widget still shows the guide.",
                    },
                ),
                "style": (list(STYLES), {"default": "none", "tooltip": "Rendering medium only. The person and outfit stay."}),
            },
        }

    @classmethod
    def VALIDATE_INPUTS(cls, state_json, use_layout_image=False, style="none"):
        try:
            compile_sheet(
                state_json,
                use_layout=use_layout_image,
                style=style,
                presence={},
                limit=resolution_cap(),
            )
        except SheetError as exc:
            return str(exc)
        return True

    def build(
        self,
        state_json,
        character_image,
        reference_image_1=None,
        reference_image_2=None,
        reference_image_3=None,
        use_layout_image=False,
        style="none",
    ):
        _check_image(character_image, "character_image", True)
        _check_image(reference_image_1, "reference_image_1", False)
        _check_image(reference_image_2, "reference_image_2", False)
        _check_image(reference_image_3, "reference_image_3", False)
        presence = {
            "reference_image_1": reference_image_1 is not None,
            "reference_image_2": reference_image_2 is not None,
            "reference_image_3": reference_image_3 is not None,
        }
        result = compile_sheet(
            state_json,
            use_layout=use_layout_image,
            style=style,
            presence=presence,
            limit=resolution_cap(),
        )
        layout_image = None
        if use_layout_image:
            raw = render_guide(result["layout"])
            layout_image = pack_image(raw, result["width"], result["height"])
        return (
            result["prompt"],
            result["width"],
            result["height"],
            character_image,
            layout_image,
            reference_image_1,
            reference_image_2,
            reference_image_3,
        )


NODE_CLASS_MAPPINGS = {
    "DevilH3CharacterSheet": DevilH3CharacterSheet,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "DevilH3CharacterSheet": "Devil H3 Character Sheet",
}

__all__ = [
    "DevilH3CharacterSheet",
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
    "compile_sheet",
    "pack_image",
    "resolution_cap",
]
