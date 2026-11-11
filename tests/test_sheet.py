"""Prompt and layout compilation without ComfyUI."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from py.catalog import PRESETS, VIEW_ORDER  # noqa: E402
from py.figures import plan_for  # noqa: E402
from py.guide import FRAME, INK, JOINT, PAPER, render_guide  # noqa: E402
from py.layout import plan_sheet  # noqa: E402
from py.prompt import picture_map, write_prompt  # noqa: E402
from py.sheet_node import compile_sheet  # noqa: E402
from py.state import (  # noqa: E402
    DEFAULT_STATE_JSON,
    SheetError,
    default_state,
    parse_state,
    serialize_state,
)


def _state(**updates):
    state = default_state()
    state.update(updates)
    if "size" in updates:
        state["size"] = {**default_state()["size"], **updates["size"]}
    return state


class StateTests(unittest.TestCase):
    def test_default_round_trip_orders_views(self):
        raw = json.dumps({
            "footwear": "follow",
            "outfit_shape": "follow",
            "hands": "follow",
            "roles": {
                "reference_image_3": "same_character",
                "reference_image_1": "same_character",
                "reference_image_2": "same_character",
            },
            "notes": {},
            "size": {"height": 1280, "width": 2208, "panel_height": 1120, "mode": "auto"},
            "views": ["body_back", "face_front", "face_front", "body_front", "face_left", "body_left"],
            "version": 1,
        })
        parsed = parse_state(raw)
        self.assertEqual(parsed["views"], list(PRESETS["five"]))
        self.assertEqual(serialize_state(parsed), DEFAULT_STATE_JSON)

    def test_rejects_bad_documents(self):
        base = json.loads(DEFAULT_STATE_JSON)
        cases = [
            DEFAULT_STATE_JSON.replace('"version":1', '"version":1.0'),
            DEFAULT_STATE_JSON.replace("1120", "1120.0"),
            DEFAULT_STATE_JSON.replace("1120", "true"),
            DEFAULT_STATE_JSON + "x",
            "{",
            '{"version":1,"version":1}',
        ]
        for raw in cases:
            with self.assertRaises(SheetError):
                parse_state(raw)
        base["views"] = []
        with self.assertRaises(SheetError) as empty:
            parse_state(json.dumps(base))
        self.assertEqual(empty.exception.code, "views")
        base = json.loads(DEFAULT_STATE_JSON)
        base["views"] = ["not_a_view"]
        with self.assertRaises(SheetError):
            parse_state(json.dumps(base))
        base = json.loads(DEFAULT_STATE_JSON)
        base["size"]["panel_height"] = 31
        with self.assertRaises(SheetError) as small:
            parse_state(json.dumps(base))
        self.assertEqual(small.exception.code, "size")
        base = json.loads(DEFAULT_STATE_JSON)
        base["extra"] = 1
        with self.assertRaises(SheetError) as extra:
            parse_state(json.dumps(base))
        self.assertEqual(extra.exception.code, "keys")
        base = json.loads(DEFAULT_STATE_JSON)
        base["roles"]["reference_image_1"] = "cape"
        with self.assertRaises(SheetError) as role:
            parse_state(json.dumps(base))
        self.assertEqual(role.exception.code, "role")

    def test_note_limits_and_blanks(self):
        state = default_state()
        state["notes"] = {"head_hair": "   \n", "face": "freckles"}
        parsed = parse_state(serialize_state(state))
        self.assertEqual(parsed["notes"], {"face": "freckles"})
        state["notes"] = {"hands": "a" * 1001}
        with self.assertRaises(SheetError) as too_long:
            parse_state(serialize_state(state))
        self.assertEqual(too_long.exception.code, "note_length")
        state["notes"] = {"hands": "👍" * 500}
        parsed = parse_state(serialize_state(state))
        self.assertEqual(parsed["notes"]["hands"], "👍" * 500)
        state["notes"] = {"hands": "👍" * 501}
        with self.assertRaises(SheetError):
            parse_state(serialize_state(state))


class LayoutTests(unittest.TestCase):
    def test_auto_five_is_multiple_of_32_and_grows_for_bodies(self):
        layout = plan_sheet(default_state())
        self.assertEqual((layout["width"], layout["height"]), (2784, 1248))
        self.assertEqual(layout["panels"][0]["rect"], [0.001437, 0.003205, 0.229885, 0.99359])
        self.assertEqual(layout["feet_y"], 0.996795)
        self.assertGreater(layout["width"], layout["height"])
        ids = [panel["id"] for panel in layout["panels"]]
        self.assertEqual(ids, list(PRESETS["five"]))
        panels = {panel["id"]: panel["rect"] for panel in layout["panels"]}
        self.assertLess(panels["face_front"][0], panels["face_left"][0])
        self.assertAlmostEqual(panels["face_front"][1], panels["face_left"][1], places=3)
        self.assertLess(panels["face_left"][0], panels["body_front"][0])
        self.assertLess(panels["body_front"][0], panels["body_left"][0])
        self.assertLess(panels["body_left"][0], panels["body_back"][0])
        self.assertIsNotNone(layout["feet_y"])

    def test_seven_stacks_portraits_and_puts_hands_over_feet(self):
        state = default_state()
        state["views"] = list(PRESETS["seven"])
        layout = plan_sheet(state)
        self.assertEqual((layout["width"], layout["height"]), (2784, 1248))
        panels = {panel["id"]: panel["rect"] for panel in layout["panels"]}
        self.assertAlmostEqual(panels["face_front"][0], panels["face_left"][0], places=3)
        self.assertLess(panels["face_front"][1], panels["face_left"][1])
        self.assertLess(panels["face_front"][0], panels["body_front"][0])
        self.assertLess(panels["body_front"][0], panels["body_left"][0])
        self.assertLess(panels["body_left"][0], panels["body_back"][0])
        self.assertAlmostEqual(panels["hands"][0], panels["feet"][0], places=3)
        self.assertLess(panels["hands"][1], panels["feet"][1])
        self.assertGreater(panels["hands"][0], panels["body_back"][0])

    def test_manual_keeps_the_canvas(self):
        state = default_state()
        state["size"] = {**state["size"], "mode": "manual", "width": 2048, "height": 1024}
        layout = plan_sheet(state)
        self.assertEqual(layout["width"], 2048)
        self.assertEqual(layout["height"], 1024)

    def test_detail_has_every_view_once(self):
        state = default_state()
        state["views"] = list(VIEW_ORDER)
        layout = plan_sheet(state)
        self.assertEqual([panel["id"] for panel in layout["panels"]], list(VIEW_ORDER))

    def test_turnaround_is_three_bodies(self):
        state = default_state()
        state["views"] = list(PRESETS["turnaround"])
        layout = plan_sheet(state)
        self.assertEqual([panel["id"] for panel in layout["panels"]], ["body_front", "body_left", "body_back"])
        self.assertIsNotNone(layout["feet_y"])


class PromptTests(unittest.TestCase):
    def test_default_prompt_lists_each_view_once(self):
        result = compile_sheet(DEFAULT_STATE_JSON, use_layout=False, style="none", presence={})
        prompt = result["prompt"]
        self.assertTrue(prompt.endswith("\n"))
        self.assertIn("subject_definitions:", prompt)
        self.assertIn("[reference generation]", prompt)
        self.assertIn("fully_preserved", prompt)
        self.assertIn("[Shot 1]", prompt)
        self.assertIn("overall_soundscape:", prompt)
        self.assertIn("non_diegetic_music:", prompt)
        self.assertIn("<Picture 1>", prompt)
        self.assertNotIn("<Picture 2>", prompt)
        for view in PRESETS["five"]:
            self.assertEqual(prompt.count(f"Panel {view}:"), 1)
        self.assertNotIn("frame pixels", prompt)
        self.assertIn("rect [", prompt)
        self.assertIn("right edge", prompt)

    def test_layout_flag_changes_wording_not_canvas(self):
        off = compile_sheet(DEFAULT_STATE_JSON, use_layout=False, style="none", presence={})
        on = compile_sheet(DEFAULT_STATE_JSON, use_layout=True, style="none", presence={})
        self.assertEqual((off["width"], off["height"]), (on["width"], on["height"]))
        self.assertIn("frame pixels", on["prompt"])
        self.assertIn("<Picture 2>", on["prompt"])
        self.assertIn("placement sheet", on["prompt"])
        self.assertNotIn("frame pixels", off["prompt"])

    def test_picture_numbers_skip_gaps(self):
        state = parse_state(DEFAULT_STATE_JSON)
        state["roles"]["reference_image_2"] = "footwear"
        pictures = picture_map(state, use_layout=False, presence={
            "reference_image_1": False,
            "reference_image_2": True,
            "reference_image_3": False,
        })
        self.assertEqual([item["source"] for item in pictures], ["character_image", "reference_image_2"])
        self.assertEqual(pictures[1]["tag"], "<Picture 2>")
        self.assertEqual(pictures[1]["wire"], "ref_images.ref_image_3")
        prompt = write_prompt(state, plan_sheet(state), use_layout=False, style="none", presence={
            "reference_image_2": True,
        })
        self.assertIn("<Picture 2>", prompt)
        self.assertIn("Footwear", prompt)
        self.assertNotIn("<Picture 3>", prompt)

    def test_later_role_wins_and_style_is_medium_only(self):
        state = parse_state(DEFAULT_STATE_JSON)
        state["roles"]["reference_image_1"] = "hands"
        state["roles"]["reference_image_2"] = "hands"
        prompt = write_prompt(state, plan_sheet(state), use_layout=False, style="anime", presence={
            "reference_image_1": True,
            "reference_image_2": True,
        })
        self.assertIn("<Picture 3> wins", prompt)
        self.assertIn("anime linework", prompt)
        self.assertIn("medium only", prompt)
        self.assertIn("partially_preserved", prompt)

    def test_outfit_only_drops_the_person(self):
        state = default_state()
        state["views"] = ["clothing_front", "clothing_back"]
        prompt = write_prompt(state, plan_sheet(parse_state(serialize_state(state))), use_layout=False, style="none", presence={})
        self.assertIn("not the person wearing it", prompt)
        self.assertIn("No person", prompt)
        self.assertEqual(prompt.count("Panel clothing_front:"), 1)
        self.assertEqual(prompt.count("Panel clothing_back:"), 1)

    def test_choices_apply_only_when_relevant(self):
        state = default_state()
        state["hands"] = "bare"
        state["footwear"] = "barefoot"
        state["outfit_shape"] = "skirt"
        prompt = write_prompt(state, plan_sheet(parse_state(serialize_state(state))), use_layout=False, style="none", presence={})
        self.assertIn("bare hands", prompt)
        self.assertIn("no shoes", prompt)
        self.assertIn("skirt or robe", prompt)
        state["views"] = ["face_front"]
        prompt = write_prompt(state, plan_sheet(parse_state(serialize_state(state))), use_layout=False, style="none", presence={})
        self.assertNotIn("bare hands", prompt)
        self.assertNotIn("no shoes", prompt)

    def test_ineligible_reference_is_ignored(self):
        state = default_state()
        state["views"] = ["body_back"]
        state["roles"]["reference_image_1"] = "face"
        prompt = write_prompt(state, plan_sheet(parse_state(serialize_state(state))), use_layout=False, style="none", presence={
            "reference_image_1": True,
        })
        self.assertIn("Ignore it", prompt)

    def test_bad_style_and_flag(self):
        with self.assertRaises(SheetError):
            compile_sheet(DEFAULT_STATE_JSON, use_layout="yes", style="none", presence={})
        with self.assertRaises(SheetError):
            compile_sheet(DEFAULT_STATE_JSON, use_layout=False, style="ink", presence={})


class GuideTests(unittest.TestCase):
    def test_guide_is_deterministic_and_uses_our_ink(self):
        layout = plan_sheet(default_state())
        first = render_guide(layout)
        second = render_guide(layout)
        self.assertEqual(first, second)
        self.assertEqual(len(first), layout["width"] * layout["height"] * 3)
        image = np.frombuffer(first, dtype=np.uint8).reshape(layout["height"], layout["width"], 3)
        paper = np.all(image == np.array(PAPER, dtype=np.uint8), axis=2)
        self.assertGreater(int(paper.sum()), image.shape[0] * image.shape[1] // 2)
        for color in (FRAME, INK, JOINT):
            self.assertTrue(np.any(np.all(image == np.array(color, dtype=np.uint8), axis=2)))

    def test_profile_points_right_and_outfit_has_no_head(self):
        left = plan_for("body_left")
        self.assertTrue(any(op[0] == "line" and op[3] > op[1] for op in left))
        self.assertTrue(any(op[0] == "oval" for op in plan_for("body_front")))
        self.assertTrue(all(op[0] != "oval" for op in plan_for("clothing_front")))
        right = plan_for("face_right")
        self.assertTrue(any(op[0] == "line" and op[3] < op[1] for op in right))


if __name__ == "__main__":
    unittest.main()
