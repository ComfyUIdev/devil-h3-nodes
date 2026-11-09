"""Procedural mannequin plans in a 0..1000 box.

Each plan is a list of drawing ops. The guide renderer and the browser
widget both follow these numbers. Heads are ovals, torsos are rectangles,
and red dots mark joints. Clothing plans have no head.
"""

from __future__ import annotations

# op, then integers in 0..1000 of the panel's inner box.
Plan = tuple[tuple, ...]

BODY_FRONT: Plan = (
    ("oval", 500, 120, 90, 100),
    ("line", 500, 220, 500, 270),
    ("rect", 340, 270, 320, 260),
    ("line", 340, 310, 150, 490),
    ("line", 660, 310, 850, 490),
    ("line", 430, 530, 380, 880),
    ("line", 570, 530, 620, 880),
    ("rect", 300, 870, 150, 60),
    ("rect", 560, 870, 150, 60),
    ("rect", 445, 145, 28, 16),
    ("rect", 530, 145, 28, 16),
    ("dot", 340, 310),
    ("dot", 660, 310),
    ("dot", 430, 530),
    ("dot", 570, 530),
)

BODY_LEFT: Plan = (
    ("oval", 430, 120, 78, 100),
    ("line", 500, 125, 690, 145),
    ("line", 470, 220, 470, 270),
    ("rect", 390, 270, 170, 260),
    ("line", 470, 320, 620, 500),
    ("line", 470, 530, 520, 880),
    ("rect", 450, 870, 170, 55),
    ("rect", 455, 140, 22, 14),
    ("dot", 470, 320),
    ("dot", 470, 530),
)

BODY_BACK: Plan = (
    ("fill", 400, 30, 200, 90),
    ("oval", 500, 130, 90, 100),
    ("line", 500, 230, 500, 520),
    ("rect", 340, 270, 320, 260),
    ("line", 340, 310, 160, 490),
    ("line", 660, 310, 840, 490),
    ("line", 430, 530, 380, 880),
    ("line", 570, 530, 620, 880),
    ("rect", 300, 870, 150, 60),
    ("rect", 560, 870, 150, 60),
    ("dot", 340, 310),
    ("dot", 660, 310),
)

BUST_FRONT: Plan = (
    ("oval", 500, 280, 160, 180),
    ("line", 500, 460, 500, 540),
    ("rect", 250, 540, 500, 280),
    ("rect", 410, 320, 40, 24),
    ("rect", 550, 320, 40, 24),
    ("dot", 280, 580),
    ("dot", 720, 580),
)

BUST_LEFT: Plan = (
    ("oval", 420, 300, 140, 180),
    ("line", 540, 300, 820, 340),
    ("rect", 300, 560, 360, 260),
    ("rect", 470, 330, 30, 20),
    ("dot", 360, 600),
)

BUST_RIGHT: Plan = (
    ("oval", 580, 300, 140, 180),
    ("line", 460, 300, 180, 340),
    ("rect", 340, 560, 360, 260),
    ("rect", 500, 330, 30, 20),
    ("dot", 640, 600),
)

BUST_3Q_LEFT: Plan = (
    ("oval", 460, 290, 150, 180),
    ("line", 560, 310, 760, 350),
    ("rect", 280, 550, 420, 270),
    ("rect", 430, 330, 28, 20),
    ("rect", 520, 345, 18, 14),
    ("dot", 320, 590),
    ("dot", 660, 590),
)

BUST_3Q_RIGHT: Plan = (
    ("oval", 540, 290, 150, 180),
    ("line", 440, 310, 240, 350),
    ("rect", 300, 550, 420, 270),
    ("rect", 500, 330, 28, 20),
    ("rect", 430, 345, 18, 14),
    ("dot", 340, 590),
    ("dot", 680, 590),
)

BUST_BACK: Plan = (
    ("fill", 340, 120, 320, 140),
    ("oval", 500, 300, 160, 180),
    ("rect", 250, 540, 500, 280),
    ("line", 500, 200, 500, 700),
    ("dot", 280, 580),
    ("dot", 720, 580),
)

CLOTH_FRONT: Plan = (
    ("rect", 420, 80, 160, 70),
    ("rect", 300, 140, 400, 620),
    ("rect", 80, 160, 220, 180),
    ("rect", 700, 160, 220, 180),
    ("rect", 470, 280, 24, 24),
    ("rect", 470, 360, 24, 24),
    ("rect", 470, 440, 24, 24),
    ("line", 300, 760, 700, 760),
)

CLOTH_BACK: Plan = (
    ("rect", 420, 80, 160, 70),
    ("rect", 300, 140, 400, 620),
    ("rect", 80, 160, 220, 180),
    ("rect", 700, 160, 220, 180),
    ("line", 500, 150, 500, 740),
    ("line", 300, 760, 700, 760),
)

HANDS: Plan = (
    ("rect", 80, 280, 280, 340),
    ("rect", 90, 120, 50, 170),
    ("rect", 155, 80, 50, 210),
    ("rect", 220, 90, 50, 200),
    ("rect", 285, 150, 46, 150),
    ("rect", 620, 280, 280, 340),
    ("rect", 640, 150, 46, 150),
    ("rect", 710, 90, 50, 200),
    ("rect", 775, 80, 50, 210),
    ("rect", 840, 120, 50, 170),
    ("dot", 200, 400),
    ("dot", 780, 400),
)

FEET: Plan = (
    ("rect", 80, 360, 340, 220),
    ("rect", 80, 300, 120, 80),
    ("rect", 560, 360, 340, 220),
    ("rect", 780, 300, 120, 80),
    ("line", 80, 540, 420, 540),
    ("line", 560, 540, 900, 540),
    ("dot", 200, 420),
    ("dot", 760, 420),
)

PLANS = {
    "face_front": BUST_FRONT,
    "face_left": BUST_LEFT,
    "face_right": BUST_RIGHT,
    "face_3q_left": BUST_3Q_LEFT,
    "face_3q_right": BUST_3Q_RIGHT,
    "face_back": BUST_BACK,
    "body_front": BODY_FRONT,
    "body_left": BODY_LEFT,
    "body_back": BODY_BACK,
    "clothing_front": CLOTH_FRONT,
    "clothing_back": CLOTH_BACK,
    "hands": HANDS,
    "feet": FEET,
}


def plan_for(view_id: str) -> Plan:
    return PLANS[view_id]
