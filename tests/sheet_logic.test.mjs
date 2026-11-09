import test from "node:test";
import assert from "node:assert/strict";

import {
  DEFAULT_STATE_JSON,
  PRESETS,
  VIEW_ORDER,
  defaultState,
  parseState,
  presetName,
  serializeState,
  utf16Units,
  viewsForRole,
} from "../web/sheet_state.js";
import { planSheet } from "../web/sheet_layout.js";
import { figurePlan } from "../web/sheet_figures.js";

function clone(overrides = {}) {
  const state = defaultState();
  return {
    ...state,
    ...overrides,
    size: { ...state.size, ...(overrides.size || {}) },
    notes: { ...state.notes, ...(overrides.notes || {}) },
    roles: { ...state.roles, ...(overrides.roles || {}) },
    views: overrides.views ? [...overrides.views] : [...state.views],
  };
}

test("default JSON round-trips and canonicalizes view order", () => {
  const raw = JSON.stringify({
    footwear: "follow",
    outfit_shape: "follow",
    hands: "follow",
    roles: {
      reference_image_3: "same_character",
      reference_image_1: "same_character",
      reference_image_2: "same_character",
    },
    notes: { head_hair: "   \n", face: "freckles" },
    size: { height: 1280, width: 2208, panel_height: 1120, mode: "auto" },
    views: ["feet", "body_back", "face_front", "face_front", "body_front", "face_left", "body_left"],
    version: 1,
  });
  const parsed = parseState(raw);
  assert.deepEqual(parsed.views, ["face_front", "face_left", "body_front", "body_left", "body_back", "feet"]);
  assert.deepEqual(parsed.notes, { face: "freckles" });
  assert.equal(serializeState(parseState(DEFAULT_STATE_JSON)), DEFAULT_STATE_JSON);
  assert.equal(presetName(defaultState().views), "five");
  assert.equal(presetName(PRESETS.seven), "seven");
  assert.equal(presetName(["body_front", "hands"]), "custom");
});

test("parser rejects duplicate keys, floats, and unknown fields", () => {
  assert.throws(() => parseState('{"version":1,"version":1}'), (error) => error.code === "duplicate");
  assert.throws(() => parseState(DEFAULT_STATE_JSON.replace('"version":1', '"version":1.0')), (error) => error.code === "integer");
  assert.throws(() => parseState(DEFAULT_STATE_JSON.replace("1120", "1120.0")));
  assert.throws(() => parseState("{"));
  assert.throws(() => parseState(DEFAULT_STATE_JSON + "x"));
  const empty = clone({ views: [] });
  assert.throws(() => parseState(serializeState(empty)), (error) => error.code === "views");
  const badView = clone({ views: ["nope"] });
  assert.throws(() => parseState(serializeState(badView)), (error) => error.code === "views");
  const badSize = clone({ size: { panel_height: 31 } });
  assert.throws(() => parseState(serializeState(badSize)), (error) => error.code === "size");
  const badRole = clone();
  badRole.roles.reference_image_1 = "cape";
  assert.throws(() => parseState(serializeState(badRole)), (error) => error.code === "role");
});

test("notes count UTF-16 units and drop blanks", () => {
  assert.equal(utf16Units("a"), 1);
  assert.equal(utf16Units("👍"), 2);
  const ok = clone({ notes: { hands: "👍".repeat(500) } });
  assert.equal(utf16Units(parseState(serializeState(ok)).notes.hands), 1000);
  const tooLong = clone({ notes: { hands: "👍".repeat(501) } });
  assert.throws(() => parseState(serializeState(tooLong)), (error) => error.code === "note_length");
});

test("five-view auto layout keeps portraits side by side and bodies to the right", () => {
  const layout = planSheet(defaultState());
  assert.equal(layout.width, 2784);
  assert.equal(layout.height, 1248);
  assert.deepEqual(layout.panels[0].rect, [0.001437, 0.003205, 0.229885, 0.99359]);
  assert.equal(layout.feetY, 0.996795);
  assert.ok(layout.width > layout.height);
  const panels = Object.fromEntries(layout.panels.map((panel) => [panel.id, panel.rect]));
  assert.deepEqual(layout.panels.map((panel) => panel.id), PRESETS.five);
  assert.ok(panels.face_front[0] < panels.face_left[0]);
  assert.ok(Math.abs(panels.face_front[1] - panels.face_left[1]) < 0.001);
  assert.ok(panels.face_left[0] < panels.body_front[0]);
  assert.ok(panels.body_front[0] < panels.body_left[0]);
  assert.ok(panels.body_left[0] < panels.body_back[0]);
  assert.equal(typeof layout.feetY, "number");
});

test("seven-view layout stacks portraits and puts hands above feet", () => {
  const layout = planSheet(clone({ views: PRESETS.seven }));
  assert.equal(layout.width, 2784);
  assert.equal(layout.height, 1248);
  const panels = Object.fromEntries(layout.panels.map((panel) => [panel.id, panel.rect]));
  assert.ok(Math.abs(panels.face_front[0] - panels.face_left[0]) < 0.001);
  assert.ok(panels.face_front[1] < panels.face_left[1]);
  assert.ok(panels.body_front[0] < panels.body_left[0]);
  assert.ok(panels.body_left[0] < panels.body_back[0]);
  assert.ok(Math.abs(panels.hands[0] - panels.feet[0]) < 0.001);
  assert.ok(panels.hands[1] < panels.feet[1]);
  assert.ok(panels.hands[0] > panels.body_back[0]);
});

test("manual mode keeps the requested canvas and detail keeps every view", () => {
  const manual = planSheet(clone({ size: { mode: "manual", width: 2048, height: 1024 } }));
  assert.equal(manual.width, 2048);
  assert.equal(manual.height, 1024);
  const detail = planSheet(clone({ views: VIEW_ORDER }));
  assert.deepEqual(detail.panels.map((panel) => panel.id), VIEW_ORDER);
});

test("role visibility skips rear views for a face reference", () => {
  assert.deepEqual(viewsForRole("face", ["body_back", "face_front"]), ["face_front"]);
  assert.ok(viewsForRole("outfit_back", ["body_front", "body_left", "clothing_back"]).includes("body_left"));
  assert.ok(!viewsForRole("outfit_back", ["body_front", "body_left", "clothing_back"]).includes("body_front"));
});

test("figure plans point profiles the right way and outfits have no head", () => {
  assert.equal(figurePlan("body_front")[0][0], "oval");
  assert.ok(figurePlan("body_left").some((op) => op[0] === "line" && op[3] > op[1]));
  assert.ok(figurePlan("face_right").some((op) => op[0] === "line" && op[3] < op[1]));
  assert.ok(figurePlan("clothing_front").every((op) => op[0] !== "oval"));
  assert.ok(figurePlan("hands").some((op) => op[0] === "dot"));
});
