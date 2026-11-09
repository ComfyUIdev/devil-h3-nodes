/**
 * Sheet state shared by the node widget and the browser tests.
 * The JSON object is the value stored on state_json.
 */

export const VIEW_ORDER = Object.freeze([
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
]);

export const PRESETS = Object.freeze({
  five: ["face_front", "face_left", "body_front", "body_left", "body_back"],
  basic: ["face_front", "body_front", "body_left", "body_back"],
  turnaround: ["body_front", "body_left", "body_back"],
  single: ["body_front"],
  seven: ["face_front", "face_left", "body_front", "body_left", "body_back", "hands", "feet"],
  head: VIEW_ORDER.slice(0, 6),
  outfit: ["clothing_front", "clothing_back"],
  detail: [...VIEW_ORDER],
});

export const NOTE_IDS = Object.freeze([
  "head_hair",
  "face",
  "upper_outfit",
  "rear_outfit",
  "lower_outfit",
  "hands",
  "footwear",
  "other",
]);

export const ROLE_INPUTS = Object.freeze([
  "reference_image_1",
  "reference_image_2",
  "reference_image_3",
]);

export const ROLES = Object.freeze([
  "same_character",
  "face",
  "head",
  "outfit",
  "outfit_front",
  "outfit_back",
  "hands",
  "footwear",
]);

export const HAND_CHOICES = Object.freeze(["follow", "bare", "covered"]);
export const OUTFIT_SHAPES = Object.freeze(["follow", "pants", "skirt"]);
export const FOOTWEAR_CHOICES = Object.freeze(["follow", "shod", "barefoot"]);
export const STYLES = Object.freeze([
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
]);

export const PANEL_HEIGHT_CHOICES = Object.freeze([768, 1024, 1120, 1280, 1536]);
export const MAX_NOTE_UNITS = 1000;
export const STATE_BYTE_LIMIT = 64 * 1024;
export const LARGE_PIXEL_MARK = 1000000;

const STATE_KEYS = ["version", "views", "size", "notes", "roles", "hands", "outfit_shape", "footwear"];
const SIZE_KEYS = ["mode", "panel_height", "width", "height"];
const TRIM = /[\t\n\u000b\u000c\r \u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000\ufeff]/;

const MESSAGES = {
  type: "The sheet JSON has the wrong shape.",
  size: "Enter a whole number of at least 32, in steps of 32.",
  integer: "Enter a whole number of at least 32, in steps of 32.",
  limit: "That size is above the resolution cap.",
  views: "Choose one or more known views.",
  version: "This sheet needs version 1.",
  mode: "Size mode must be auto or manual.",
  keys: "The sheet JSON has missing or unknown fields.",
  json: "The sheet JSON could not be read.",
  duplicate: "The sheet JSON repeats a key.",
  notes: "Unknown part note.",
  note_length: "Keep each note within 1000 UTF-16 units.",
  role: "Unknown reference role.",
  choice: "Unknown appearance choice.",
  unicode: "The sheet JSON has invalid Unicode.",
};

export class SheetError extends Error {
  constructor(code, detail = "") {
    super(MESSAGES[code] || code);
    this.code = code;
    this.detail = detail;
  }
}

function fail(code, detail) {
  throw new SheetError(code, detail);
}

export function utf16Units(text) {
  let count = 0;
  for (const char of text) {
    count += char.codePointAt(0) > 0xffff ? 2 : 1;
  }
  return count;
}

export function isBlank(text) {
  let start = 0;
  let end = text.length;
  while (start < end && TRIM.test(text[start])) start += 1;
  while (end > start && TRIM.test(text[end - 1])) end -= 1;
  return start === end;
}

function exactKeys(value, keys, label) {
  if (!value || typeof value !== "object" || Array.isArray(value)) fail("type", label);
  const actual = Object.keys(value);
  if (actual.length !== keys.length || keys.some((key) => !Object.hasOwn(value, key))) {
    fail("keys", label);
  }
}

function pixels(value, label, cap) {
  if (typeof value !== "number" || !Number.isInteger(value)) fail("integer", label);
  if (value < 32 || value % 32 !== 0) fail("size", label);
  if (value > cap) fail("limit", label);
  return value;
}

export function parseJson(text) {
  if (typeof text !== "string") fail("type", "state");
  if (new TextEncoder().encode(text).length > STATE_BYTE_LIMIT) fail("size", "state");
  let index = 0;
  const skip = () => {
    while (text[index] === " " || text[index] === "\n" || text[index] === "\r" || text[index] === "\t") index += 1;
  };
  const parseString = () => {
    index += 1;
    let out = "";
    while (index < text.length) {
      const char = text[index];
      if (char === '"') {
        index += 1;
        return out;
      }
      if (char === "\\") {
        index += 1;
        const esc = text[index];
        const simple = { '"': '"', "\\": "\\", "/": "/", b: "\b", f: "\f", n: "\n", r: "\r", t: "\t" };
        if (Object.hasOwn(simple, esc)) {
          out += simple[esc];
          index += 1;
          continue;
        }
        if (esc === "u") {
          const hex = text.slice(index + 1, index + 5);
          if (!/^[0-9a-fA-F]{4}$/.test(hex)) fail("json", "state");
          const code = Number.parseInt(hex, 16);
          index += 5;
          if (code >= 0xd800 && code <= 0xdbff) {
            if (!(text[index] === "\\" && text[index + 1] === "u")) fail("unicode", "state");
            const hex2 = text.slice(index + 2, index + 6);
            if (!/^[0-9a-fA-F]{4}$/.test(hex2)) fail("unicode", "state");
            const code2 = Number.parseInt(hex2, 16);
            if (code2 < 0xdc00 || code2 > 0xdfff) fail("unicode", "state");
            out += String.fromCodePoint(0x10000 + ((code - 0xd800) << 10) + (code2 - 0xdc00));
            index += 6;
            continue;
          }
          if (code >= 0xdc00 && code <= 0xdfff) fail("unicode", "state");
          out += String.fromCharCode(code);
          continue;
        }
        fail("json", "state");
      }
      if (char < " ") fail("json", "state");
      out += char;
      index += 1;
    }
    fail("json", "state");
  };
  const parseNumber = () => {
    const start = index;
    if (text[index] === "-") index += 1;
    if (text[index] === "0") index += 1;
    else if (text[index] >= "1" && text[index] <= "9") {
      while (text[index] >= "0" && text[index] <= "9") index += 1;
    } else fail("json", "state");
    let fractional = false;
    if (text[index] === ".") {
      fractional = true;
      index += 1;
      if (!(text[index] >= "0" && text[index] <= "9")) fail("json", "state");
      while (text[index] >= "0" && text[index] <= "9") index += 1;
    }
    if (text[index] === "e" || text[index] === "E") {
      fractional = true;
      index += 1;
      if (text[index] === "+" || text[index] === "-") index += 1;
      if (!(text[index] >= "0" && text[index] <= "9")) fail("json", "state");
      while (text[index] >= "0" && text[index] <= "9") index += 1;
    }
    const token = text.slice(start, index);
    const value = Number(token);
    if (!Number.isFinite(value)) fail("json", "state");
    return fractional ? { float: value } : value;
  };
  const parseValue = () => {
    skip();
    const char = text[index];
    if (char === "{") return parseObject();
    if (char === "[") return parseArray();
    if (char === '"') return parseString();
    if (char === "-" || (char >= "0" && char <= "9")) return parseNumber();
    if (text.startsWith("true", index)) {
      index += 4;
      return true;
    }
    if (text.startsWith("false", index)) {
      index += 5;
      return false;
    }
    if (text.startsWith("null", index)) {
      index += 4;
      return null;
    }
    fail("json", "state");
  };
  const parseObject = () => {
    index += 1;
    const obj = {};
    skip();
    if (text[index] === "}") {
      index += 1;
      return obj;
    }
    while (index < text.length) {
      skip();
      if (text[index] !== '"') fail("json", "state");
      const key = parseString();
      if (Object.hasOwn(obj, key)) fail("duplicate", key);
      skip();
      if (text[index] !== ":") fail("json", "state");
      index += 1;
      obj[key] = parseValue();
      skip();
      if (text[index] === "}") {
        index += 1;
        return obj;
      }
      if (text[index] !== ",") fail("json", "state");
      index += 1;
    }
    fail("json", "state");
  };
  const parseArray = () => {
    index += 1;
    const list = [];
    skip();
    if (text[index] === "]") {
      index += 1;
      return list;
    }
    while (index < text.length) {
      list.push(parseValue());
      skip();
      if (text[index] === "]") {
        index += 1;
        return list;
      }
      if (text[index] !== ",") fail("json", "state");
      index += 1;
    }
    fail("json", "state");
  };
  const value = parseValue();
  skip();
  if (index !== text.length) fail("json", "state");
  return value;
}

function asData(value) {
  if (value && typeof value === "object" && Object.hasOwn(value, "float")) fail("integer", "number");
  return value;
}

export function defaultState() {
  return {
    version: 1,
    views: [...PRESETS.five],
    size: { mode: "auto", panel_height: 1120, width: 2208, height: 1280 },
    notes: {},
    roles: {
      reference_image_1: "same_character",
      reference_image_2: "same_character",
      reference_image_3: "same_character",
    },
    hands: "follow",
    outfit_shape: "follow",
    footwear: "follow",
  };
}

export function serializeState(state) {
  const notes = {};
  for (const key of NOTE_IDS) if (Object.hasOwn(state.notes, key)) notes[key] = state.notes[key];
  const payload = {
    version: 1,
    views: [...state.views],
    size: {
      mode: state.size.mode,
      panel_height: state.size.panel_height,
      width: state.size.width,
      height: state.size.height,
    },
    notes,
    roles: {
      reference_image_1: state.roles.reference_image_1,
      reference_image_2: state.roles.reference_image_2,
      reference_image_3: state.roles.reference_image_3,
    },
    hands: state.hands,
    outfit_shape: state.outfit_shape,
    footwear: state.footwear,
  };
  return JSON.stringify(payload);
}

export const DEFAULT_STATE_JSON = serializeState(defaultState());

export function parseState(raw, cap = 16384) {
  if (!Number.isInteger(cap) || cap < 32) fail("limit", "cap");
  const state = parseJson(raw);
  exactKeys(state, STATE_KEYS, "state");
  if (asData(state.version) !== 1) fail("version", "state");
  if (!Array.isArray(state.views) || state.views.some((view) => typeof view !== "string")) fail("type", "views");
  if (!state.views.length) fail("views", "empty");
  if (state.views.some((view) => !VIEW_ORDER.includes(view))) fail("views", "unknown");
  exactKeys(state.size, SIZE_KEYS, "size");
  const mode = state.size.mode;
  if (mode !== "auto" && mode !== "manual") fail("mode", "size");
  const size = {
    mode,
    panel_height: pixels(asData(state.size.panel_height), "panel_height", cap),
    width: pixels(asData(state.size.width), "width", cap),
    height: pixels(asData(state.size.height), "height", cap),
  };
  if (!state.notes || typeof state.notes !== "object" || Array.isArray(state.notes)) fail("type", "notes");
  if (Object.keys(state.notes).some((key) => !NOTE_IDS.includes(key))) fail("notes", "unknown");
  const notes = {};
  for (const key of NOTE_IDS) {
    if (!Object.hasOwn(state.notes, key)) continue;
    const text = state.notes[key];
    if (typeof text !== "string") fail("type", key);
    if (utf16Units(text) > MAX_NOTE_UNITS) fail("note_length", key);
    if (!isBlank(text)) notes[key] = text;
  }
  exactKeys(state.roles, ROLE_INPUTS, "roles");
  const roles = {};
  for (const key of ROLE_INPUTS) {
    if (!ROLES.includes(state.roles[key])) fail("role", key);
    roles[key] = state.roles[key];
  }
  if (!HAND_CHOICES.includes(state.hands)) fail("choice", "hands");
  if (!OUTFIT_SHAPES.includes(state.outfit_shape)) fail("choice", "outfit_shape");
  if (!FOOTWEAR_CHOICES.includes(state.footwear)) fail("choice", "footwear");
  return {
    version: 1,
    views: VIEW_ORDER.filter((view) => state.views.includes(view)),
    size,
    notes,
    roles,
    hands: state.hands,
    outfit_shape: state.outfit_shape,
    footwear: state.footwear,
  };
}

export function presetName(views) {
  const key = views.join(",");
  for (const [name, preset] of Object.entries(PRESETS)) {
    if (preset.join(",") === key) return name;
  }
  return "custom";
}

const PART_VIEWS = {
  head_hair: [...VIEW_ORDER.slice(0, 6), "body_front", "body_left", "body_back"],
  face: ["face_front", "face_left", "face_right", "face_3q_left", "face_3q_right", "body_front", "body_left"],
  upper_outfit: [...VIEW_ORDER.slice(0, 9), "clothing_front", "clothing_back"],
  rear_outfit: ["face_back", "body_left", "body_back", "clothing_back"],
  lower_outfit: ["body_front", "body_left", "body_back", "clothing_front", "clothing_back"],
  hands: ["body_front", "body_left", "body_back", "hands"],
  footwear: ["body_front", "body_left", "body_back", "feet"],
  other: [...VIEW_ORDER],
};

const REAR = new Set(["face_back", "body_back", "clothing_back"]);
const ROLE_PARTS = {
  face: ["face"],
  head: ["head_hair", "face"],
  outfit: ["upper_outfit", "rear_outfit", "lower_outfit"],
  outfit_front: ["upper_outfit", "lower_outfit"],
  outfit_back: ["rear_outfit", "lower_outfit"],
  hands: ["hands"],
  footwear: ["footwear"],
};

export function viewsForRole(role, selected) {
  if (role === "same_character") return [...selected];
  const parts = ROLE_PARTS[role] || [];
  return selected.filter((view) => {
    if (role === "face" && REAR.has(view)) return false;
    if (role === "outfit_front" && REAR.has(view)) return false;
    if (role === "outfit_back" && !REAR.has(view) && view !== "body_left") return false;
    return parts.some((part) => PART_VIEWS[part].includes(view));
  });
}
