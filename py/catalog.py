"""View catalog, presets, and appearance choices for the Devil H3 sheet.

The ids are stable wiring tokens. Labels and camera lines are the words we
send to MiniMax H3. Nothing here reads the disk or the network.
"""

from __future__ import annotations

VIEW_ORDER = (
    "face_front",
    "face_left",
    "face_right",
    "face_3q_left",
    "face_3q_right",
    "face_back",
    "body_front",
    "body_left",
    "body_back",
    "clothing_front",
    "clothing_back",
    "hands",
    "feet",
)

HEADS = VIEW_ORDER[:6]
BODIES = ("body_front", "body_left", "body_back")
CLOTHES = ("clothing_front", "clothing_back")
DETAILS = ("hands", "feet")
# The original seven-slot sheet. The full set uses the stacked seven-view
# arrangement; any smaller subset of these ids keeps the older columns.
LEGACY = (
    "face_front",
    "face_left",
    "body_front",
    "body_left",
    "body_back",
    "hands",
    "feet",
)
SEVEN = LEGACY

REAR = frozenset(("face_back", "body_back", "clothing_back"))

PRESETS = {
    "five": ("face_front", "face_left", "body_front", "body_left", "body_back"),
    "basic": ("face_front", "body_front", "body_left", "body_back"),
    "turnaround": BODIES,
    "single": ("body_front",),
    "seven": ("face_front", "face_left", "body_front", "body_left", "body_back", "hands", "feet"),
    "head": HEADS,
    "outfit": CLOTHES,
    "detail": VIEW_ORDER,
}

NOTE_IDS = (
    "head_hair",
    "face",
    "upper_outfit",
    "rear_outfit",
    "lower_outfit",
    "hands",
    "footwear",
    "other",
)

NOTE_LABELS = {
    "head_hair": "head and hair",
    "face": "face",
    "upper_outfit": "upper outfit",
    "rear_outfit": "rear outfit",
    "lower_outfit": "lower outfit",
    "hands": "hands",
    "footwear": "footwear",
    "other": "other details",
}

# Which selected views can show each note. Clothing panels are flat garments,
# so hair, face, hands, and footwear never land on them.
PART_VIEWS = {
    "head_hair": HEADS + BODIES,
    "face": ("face_front", "face_left", "face_right", "face_3q_left", "face_3q_right", "body_front", "body_left"),
    "upper_outfit": HEADS + BODIES + CLOTHES,
    "rear_outfit": ("face_back", "body_left", "body_back", "clothing_back"),
    "lower_outfit": BODIES + CLOTHES,
    "hands": BODIES + ("hands",),
    "footwear": BODIES + ("feet",),
    "other": VIEW_ORDER,
}

ROLE_INPUTS = ("reference_image_1", "reference_image_2", "reference_image_3")

ROLES = (
    "same_character",
    "face",
    "head",
    "outfit",
    "outfit_front",
    "outfit_back",
    "hands",
    "footwear",
)

ROLE_LABELS = {
    "same_character": "Same character",
    "face": "Face",
    "head": "Head/face/hair",
    "outfit": "Complete outfit",
    "outfit_front": "Outfit front",
    "outfit_back": "Outfit back",
    "hands": "Hands",
    "footwear": "Footwear",
}

# Dedicated roles map onto part notes. same_character is a supplement, not a part.
ROLE_PARTS = {
    "face": ("face",),
    "head": ("head_hair", "face"),
    "outfit": ("upper_outfit", "rear_outfit", "lower_outfit"),
    "outfit_front": ("upper_outfit", "lower_outfit"),
    "outfit_back": ("rear_outfit", "lower_outfit"),
    "hands": ("hands",),
    "footwear": ("footwear",),
}

HAND_CHOICES = ("follow", "bare", "covered")
OUTFIT_SHAPES = ("follow", "pants", "skirt")
FOOTWEAR_CHOICES = ("follow", "shod", "barefoot")

STYLES = (
    "none",
    "anime",
    "photo",
    "realistic_painting",
    "semi_realistic_anime",
    "oil_painting",
    "watercolor",
    "gouache",
    "colored_pencil",
    "cg3d",
)

STYLE_LINES = {
    "none": "",
    "anime": "Draw with crisp anime linework and flat cel color.",
    "photo": "Render the sheet as a photograph with natural surface shading.",
    "realistic_painting": "Render the sheet as a realistic painting.",
    "semi_realistic_anime": "Use anime linework with soft modeled shading.",
    "oil_painting": "Render with visible oil-paint brush texture.",
    "watercolor": "Render with watercolor washes and readable edges.",
    "gouache": "Render with opaque gouache color blocks.",
    "colored_pencil": "Render with colored-pencil strokes.",
    "cg3d": "Render as a 3D character with smooth surfaces.",
}

# Short camera directions. Profile facing follows the H3 sheet convention:
# anatomical left points toward the right edge, anatomical right toward the left.
CAMERAS = {
    "face_front": "Front bust, hair through the upper chest, both eyes visible. Stop above the waist.",
    "face_left": "Strict profile of the anatomical left side. The nose points toward the right edge. One eye. Hair through the upper chest.",
    "face_right": "Strict profile of the anatomical right side. The nose points toward the left edge. One eye. Do not mirror asymmetric features. Hair through the upper chest.",
    "face_3q_left": "Three-quarter bust from the anatomical left, about 45 degrees. The nose points toward the right edge. Both eyes, the far eye smaller. Hair through the upper chest.",
    "face_3q_right": "Three-quarter bust from the anatomical right, about 45 degrees. The nose points toward the left edge. Both eyes, the far eye smaller. Hair through the upper chest.",
    "face_back": "Rear bust, back of the head and hair through the upper chest. No face. Do not turn the head.",
    "body_front": "Full body, front, standing still. The whole figure from the top of the hair to both soles, with a gap above the hair and below the soles.",
    "body_left": "Full body, strict profile of the anatomical left side, standing still. Nose, chest, and toes point toward the right edge. Include hair through both soles.",
    "body_back": "Full body from directly behind, standing still. Hair through both soles. No face. Do not turn the head.",
    "clothing_front": "Flat front of the outfit only, neckline to the lowest hem, on white. No person, skin, head, or limbs. Sleeves stay empty.",
    "clothing_back": "Flat back of the outfit only, neckline to the lowest hem, on white. No person, skin, head, or limbs. Sleeves stay empty.",
    "hands": "One close view of exactly two hands, a left and a right, cropped at the wrists. No head or body.",
    "feet": "One close view of exactly two feet or shoes, a left and a right, including tall shafts. Closed shoes stay closed. No head or body.",
}

VIEW_LABELS = {
    "face_front": "front bust",
    "face_left": "left-profile bust",
    "face_right": "right-profile bust",
    "face_3q_left": "left three-quarter bust",
    "face_3q_right": "right three-quarter bust",
    "face_back": "rear bust",
    "body_front": "front full body",
    "body_left": "left-profile full body",
    "body_back": "rear full body",
    "clothing_front": "flat outfit front",
    "clothing_back": "flat outfit back",
    "hands": "both hands",
    "feet": "both feet",
}

PANEL_HEIGHT_CHOICES = (768, 1024, 1120, 1280, 1536)
DEFAULT_PANEL_HEIGHT = 1120
DEFAULT_MANUAL_WIDTH = 2208
DEFAULT_MANUAL_HEIGHT = 1280
MAX_NOTE_UNITS = 1000
STATE_BYTE_LIMIT = 64 * 1024
DEFAULT_RESOLUTION_CAP = 16384
# Warn in the widget when the sheet is larger than this many pixels.
LARGE_PIXEL_MARK = 1_000_000


def preset_name(views: list[str] | tuple[str, ...]) -> str:
    key = tuple(views)
    for name, preset in PRESETS.items():
        if preset == key:
            return name
    return "custom"


def views_for_note(note_id: str, selected: list[str] | tuple[str, ...]) -> tuple[str, ...]:
    allowed = PART_VIEWS[note_id]
    return tuple(view for view in selected if view in allowed)


def views_for_role(role: str, selected: list[str] | tuple[str, ...]) -> tuple[str, ...]:
    """Views where a dedicated reference is allowed to change appearance."""
    if role == "same_character":
        return tuple(selected)
    parts = ROLE_PARTS[role]
    found = []
    for view in selected:
        if role == "face" and view in REAR:
            continue
        if role == "outfit_front" and view in REAR:
            continue
        if role == "outfit_back" and view not in REAR and view != "body_left":
            continue
        if any(view in PART_VIEWS[part] for part in parts):
            found.append(view)
    return tuple(found)
