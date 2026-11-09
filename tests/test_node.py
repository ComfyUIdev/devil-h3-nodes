"""Node outputs, image pass-through, and the example workflow wiring."""

from __future__ import annotations

import json
import sys
import types
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from py.sheet_node import DevilH3CharacterSheet  # noqa: E402
from py.state import DEFAULT_STATE_JSON  # noqa: E402


class Image:
    def __init__(self, marker):
        self.marker = marker
        self.shape = (1, 8, 8, 3)


class NodeTests(unittest.TestCase):
    def test_pack_registers_one_node(self):
        from py.sheet_node import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

        text = (ROOT / "__init__.py").read_text(encoding="utf-8")
        self.assertIn("NODE_CLASS_MAPPINGS", text)
        self.assertIn('WEB_DIRECTORY = "./web"', text)
        self.assertIn("DevilH3CharacterSheet", NODE_CLASS_MAPPINGS)
        self.assertEqual(NODE_DISPLAY_NAME_MAPPINGS["DevilH3CharacterSheet"], "Devil H3 Character Sheet")
        self.assertEqual(DevilH3CharacterSheet.CATEGORY, "Devil Nodes/H3")
        self.assertEqual(
            list(DevilH3CharacterSheet.RETURN_NAMES),
            [
                "prompt",
                "width",
                "height",
                "character_image",
                "layout_image",
                "reference_image_1",
                "reference_image_2",
                "reference_image_3",
            ],
        )

    def test_passes_images_through_and_hides_the_guide(self):
        node = DevilH3CharacterSheet()
        character = Image("person")
        second = Image("boots")
        prompt, width, height, out_character, layout, ref1, ref2, ref3 = node.build(
            DEFAULT_STATE_JSON,
            character,
            reference_image_1=None,
            reference_image_2=second,
            use_layout_image=False,
            style="none",
        )
        self.assertIsInstance(prompt, str)
        self.assertIn("<Picture 2>", prompt)
        self.assertIsInstance(width, int)
        self.assertIsInstance(height, int)
        self.assertIs(out_character, character)
        self.assertIsNone(layout)
        self.assertIsNone(ref1)
        self.assertIs(ref2, second)
        self.assertIsNone(ref3)

    def test_layout_image_matches_the_canvas(self):
        torch = types.ModuleType("torch")

        class Tensor:
            def __init__(self, array):
                self.array = array
                self.shape = array.shape

            def unsqueeze(self, axis):
                return Tensor(np.expand_dims(self.array, axis))

        def from_numpy(array):
            return Tensor(array)

        torch.from_numpy = from_numpy
        previous = sys.modules.get("torch")
        sys.modules["torch"] = torch
        try:
            node = DevilH3CharacterSheet()
            character = Image("person")
            result = node.build(DEFAULT_STATE_JSON, character, use_layout_image=True, style="none")
        finally:
            if previous is None:
                sys.modules.pop("torch", None)
            else:
                sys.modules["torch"] = previous
        layout = result[4]
        self.assertEqual(layout.shape, (1, result[2], result[1], 3))
        self.assertEqual(layout.array.dtype, np.float32)
        self.assertGreaterEqual(float(layout.array.min()), 0.0)
        self.assertLessEqual(float(layout.array.max()), 1.0)
        self.assertIs(result[3], character)

    def test_rejects_a_missing_or_bad_image(self):
        node = DevilH3CharacterSheet()
        with self.assertRaises(Exception):
            node.build(DEFAULT_STATE_JSON, None)
        bad = Image("bad")
        bad.shape = (8, 8)
        with self.assertRaises(Exception):
            node.build(DEFAULT_STATE_JSON, bad)

    def test_validate_inputs(self):
        self.assertTrue(DevilH3CharacterSheet.VALIDATE_INPUTS(DEFAULT_STATE_JSON, False, "none"))
        self.assertIsInstance(DevilH3CharacterSheet.VALIDATE_INPUTS("{", False, "none"), str)

    def test_workflow_wires_native_h3_slots(self):
        data = json.loads((ROOT / "workflows" / "devil_h3_character_sheet.json").read_text(encoding="utf-8"))
        nodes = {node["type"]: node for node in data["nodes"]}
        self.assertIn("DevilH3CharacterSheet", nodes)
        self.assertIn("MiniMaxH3ReferenceToVideo", nodes)
        self.assertIn("UNETLoader", nodes)
        self.assertIn("CLIPLoader", nodes)
        self.assertIn("VAELoader", nodes)
        designer = nodes["DevilH3CharacterSheet"]["id"]
        h3 = nodes["MiniMaxH3ReferenceToVideo"]["id"]
        clip = nodes["CLIPLoader"]
        self.assertEqual(clip["widgets_values"][1], "minimax")
        links = data["links"]

        def linked(origin, slot, target, target_slot):
            return any(
                item[1] == origin and item[2] == slot and item[3] == target and item[4] == target_slot
                for item in links
            )

        self.assertTrue(linked(designer, 0, h3, 11))
        self.assertTrue(linked(designer, 1, h3, 12))
        self.assertTrue(linked(designer, 2, h3, 13))
        self.assertTrue(linked(designer, 3, h3, 3))
        self.assertTrue(linked(designer, 4, h3, 4))
        self.assertTrue(linked(designer, 5, h3, 5))
        self.assertTrue(linked(designer, 6, h3, 14))
        self.assertTrue(linked(designer, 7, h3, 15))
        h3_node = nodes["MiniMaxH3ReferenceToVideo"]
        self.assertEqual(h3_node["widgets_values"][3], 5)
        self.assertEqual(h3_node["widgets_values"][4], "match")
        batch = nodes["ImageFromBatch"]["widgets_values"]
        self.assertEqual(batch, [0, 1])


if __name__ == "__main__":
    unittest.main()
