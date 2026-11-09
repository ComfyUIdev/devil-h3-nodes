"""Devil H3 Nodes — a MiniMax H3 character-sheet designer for ComfyUI.

The pack entry merges node mappings and serves the files in ``web/``.
"""

from .py.sheet_node import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

WEB_DIRECTORY = "./web"

__all__ = [
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
    "WEB_DIRECTORY",
]
