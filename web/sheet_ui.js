/**
 * Squared sheet widget: view picker, size, roles, and the layout guide.
 * The guide is drawn here whether or not the layout image is passed to H3.
 */

import {
  FOOTWEAR_CHOICES,
  HAND_CHOICES,
  NOTE_IDS,
  OUTFIT_SHAPES,
  PANEL_HEIGHT_CHOICES,
  PRESETS,
  ROLE_INPUTS,
  ROLES,
  STYLES,
  VIEW_ORDER,
  LARGE_PIXEL_MARK,
  presetName,
} from "./sheet_state.js";
import { drawFigure } from "./sheet_figures.js";
import { VIEW_GRID_COLUMNS } from "./sheet_metrics.js";

const STYLE_ID = "devil-h3-sheet-style";

const CSS = `
.dv-sheet{box-sizing:border-box;display:flex;flex-direction:column;align-self:stretch;justify-self:stretch;width:100%;min-width:0;height:100%;min-height:0;margin:0;padding:0;overflow-x:hidden;overflow-y:auto;background:#120c0b;color:#fff7f4;font:12px/1.35 "Arial Narrow","Franklin Gothic Medium","Nimbus Sans Narrow","Liberation Sans Narrow",Impact,sans-serif;border-radius:0;pointer-events:auto;}
.dv-body{box-sizing:border-box;display:flex;flex-direction:column;flex:0 0 auto;gap:8px;width:100%;max-width:100%;min-width:0;padding:10px 12px 14px;}
.dv-sheet *{box-sizing:border-box;border-radius:0;}
.dv-mark,.dv-row,.dv-block,.dv-stage,.dv-wide{width:100%;max-width:100%;min-width:0;}
.dv-mark{display:flex;align-items:stretch;gap:8px;margin:0;}
.dv-bar{width:4px;background:#e25b45;flex:none;}
.dv-mark h1{margin:0;color:#e6ff3a;font-size:18px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;line-height:1;}
.dv-mark p{margin:2px 0 0;color:#c9b2ac;font-size:11px;letter-spacing:.04em;text-transform:uppercase;}
.dv-row{display:flex;flex-wrap:wrap;gap:8px;align-items:flex-end;}
.dv-field{display:flex;flex-direction:column;gap:3px;flex:1 1 140px;min-width:0;max-width:100%;}
.dv-wide{flex:1 1 100%;}
.dv-field span,.dv-kicker{color:#c9b2ac;font-size:10px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;}
.dv-sheet select,.dv-sheet input,.dv-sheet textarea{box-sizing:border-box;width:100%;max-width:100%;border:1px solid #5a3330;background:#1c1412;color:#fff7f4;font:12px/1.3 "Arial Narrow","Franklin Gothic Medium","Liberation Sans Narrow",sans-serif;padding:4px 6px;}
.dv-sheet input[type="checkbox"]{width:auto;max-width:none;}
.dv-sheet select:focus,.dv-sheet input:focus,.dv-sheet textarea:focus{outline:1px solid #e6ff3a;border-color:#e6ff3a;}
.dv-sheet textarea{min-height:72px;resize:vertical;}
.dv-seg{display:inline-flex;border:1px solid #5a3330;max-width:100%;}
.dv-seg button{height:26px;padding:0 10px;border:0;background:#1c1412;color:#c9b2ac;font:700 11px/1 "Arial Narrow","Franklin Gothic Medium",sans-serif;letter-spacing:.06em;text-transform:uppercase;cursor:pointer;}
.dv-seg button + button{border-left:1px solid #5a3330;}
.dv-seg button.on{background:#e25b45;color:#1a100e;}
.dv-views{display:grid;grid-template-columns:${VIEW_GRID_COLUMNS};gap:6px;width:100%;max-width:100%;min-width:0;}
.dv-view{display:flex;flex-direction:column;align-items:center;gap:4px;width:100%;min-width:0;padding:4px;border:1px solid #5a3330;background:#1c1412;color:#fff7f4;cursor:pointer;font:700 10px/1.15 "Arial Narrow","Franklin Gothic Medium",sans-serif;letter-spacing:.04em;text-transform:uppercase;}
.dv-view.on{border-color:#e6ff3a;background:#2a1814;color:#e6ff3a;}
.dv-view:hover{border-color:#e25b45;}
.dv-mini{width:56px;height:64px;background:#f7f4ef;display:block;}
.dv-stage{background:#0e0c0b;border:1px solid #5a3330;padding:6px;}
.dv-stage canvas{display:block;width:100%;height:220px;}
.dv-read{color:#e6ff3a;font-weight:700;letter-spacing:.06em;}
.dv-note{color:#c9b2ac;font-size:11px;}
.dv-error{color:#ffb1a3;font-size:11px;min-height:1em;}
.dv-check{display:flex;align-items:center;gap:6px;color:#fff7f4;font-size:12px;}
.dv-check input{accent-color:#e25b45;}
.dv-block{display:flex;flex-direction:column;gap:6px;padding-top:4px;border-top:1px solid #3a2826;}
.lg-node:has(.dv-sheet) .lg-node-widgets,
.lg-node:has(.dv-sheet) [data-testid="node-widgets"]{box-sizing:border-box;width:100% !important;max-width:100% !important;min-width:0 !important;align-self:stretch !important;justify-self:stretch !important;grid-template-columns:minmax(0,1fr) !important;}
.lg-node:has(.dv-sheet) .lg-node-widget:has(.dv-sheet),
.lg-node:has(.dv-sheet) [data-widget-name="devil_h3_sheet"]{box-sizing:border-box;width:100% !important;max-width:100% !important;min-width:0 !important;align-self:stretch !important;justify-self:stretch !important;}
.lg-node:has(.dv-sheet) .lg-node-widget:has(.dv-sheet) > *,
.lg-node:has(.dv-sheet) [data-widget-name="devil_h3_sheet"] > *{box-sizing:border-box;width:100% !important;min-width:0 !important;height:100%;}
`;

const VIEW_TITLES = {
  face_front: "Front bust",
  face_left: "Left bust",
  face_right: "Right bust",
  face_3q_left: "Left 3/4",
  face_3q_right: "Right 3/4",
  face_back: "Rear bust",
  body_front: "Front body",
  body_left: "Left body",
  body_back: "Rear body",
  clothing_front: "Outfit front",
  clothing_back: "Outfit back",
  hands: "Hands",
  feet: "Feet",
};

const PRESET_TITLES = {
  five: "Five views",
  basic: "Four views",
  turnaround: "Turnaround",
  single: "Single full body",
  seven: "Seven views, hands and feet",
  head: "Head studies",
  outfit: "Outfit front and back",
  detail: "All thirteen views",
  custom: "Custom",
};

const ROLE_TITLES = {
  same_character: "Same character",
  face: "Face",
  head: "Head/face/hair",
  outfit: "Complete outfit",
  outfit_front: "Outfit front",
  outfit_back: "Outfit back",
  hands: "Hands",
  footwear: "Footwear",
};

const NOTE_TITLES = {
  head_hair: "Head and hair",
  face: "Face",
  upper_outfit: "Upper outfit",
  rear_outfit: "Rear outfit",
  lower_outfit: "Lower outfit",
  hands: "Hands",
  footwear: "Footwear",
  other: "Other details",
};

const HAND_TITLES = { follow: "Follow reference", bare: "Bare", covered: "Covered" };
const SHAPE_TITLES = { follow: "Follow reference", pants: "Pants", skirt: "Skirt or robe" };
const FOOT_TITLES = { follow: "Follow reference", shod: "Shoes", barefoot: "Barefoot" };
const STYLE_TITLES = {
  none: "None",
  anime: "Anime",
  photo: "Photo",
  realistic_painting: "Realistic painting",
  semi_realistic_anime: "Semi-realistic anime",
  oil_painting: "Oil painting",
  watercolor: "Watercolor",
  gouache: "Gouache",
  colored_pencil: "Colored pencil",
  cg3d: "3D",
};

function ensureStyles() {
  if (typeof document === "undefined" || document.getElementById(STYLE_ID)) return;
  const style = document.createElement("style");
  style.id = STYLE_ID;
  style.textContent = CSS;
  document.head.append(style);
}

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text) node.textContent = text;
  return node;
}

function field(labelText, control) {
  const wrap = el("label", "dv-field");
  wrap.append(el("span", "", labelText), control);
  return wrap;
}

function fillSelect(select, pairs) {
  for (const [value, label] of pairs) {
    const option = el("option", "", label);
    option.value = value;
    select.append(option);
  }
}

function paint(canvas, layout) {
  const cssWidth = canvas.clientWidth || 640;
  const cssHeight = canvas.clientHeight || 220;
  const ratio = window.devicePixelRatio || 1;
  canvas.width = Math.round(cssWidth * ratio);
  canvas.height = Math.round(cssHeight * ratio);
  const ctx = canvas.getContext("2d");
  ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
  ctx.fillStyle = "#0e0c0b";
  ctx.fillRect(0, 0, cssWidth, cssHeight);
  if (!layout) return;
  const scale = Math.min((cssWidth - 12) / layout.width, (cssHeight - 12) / layout.height);
  const ox = (cssWidth - layout.width * scale) / 2;
  const oy = (cssHeight - layout.height * scale) / 2;
  ctx.fillStyle = "#f7f4ef";
  ctx.fillRect(ox, oy, layout.width * scale, layout.height * scale);
  for (const panel of layout.panels) {
    const x = ox + panel.rect[0] * layout.width * scale;
    const y = oy + panel.rect[1] * layout.height * scale;
    const w = panel.rect[2] * layout.width * scale;
    const h = panel.rect[3] * layout.height * scale;
    ctx.strokeStyle = "#1a100e";
    ctx.lineWidth = Math.max(1, scale * 3);
    ctx.strokeRect(x + 0.5, y + 0.5, Math.max(1, w - 1), Math.max(1, h - 1));
    const inset = Math.max(3, scale * 8);
    if (w > inset * 2 + 4 && h > inset * 2 + 4) {
      drawFigure(ctx, [x + inset, y + inset, w - inset * 2, h - inset * 2], panel.id);
    }
  }
}

function miniCanvas(view) {
  const canvas = el("canvas", "dv-mini");
  canvas.width = 56;
  canvas.height = 64;
  const ctx = canvas.getContext("2d");
  ctx.fillStyle = "#f7f4ef";
  ctx.fillRect(0, 0, 56, 64);
  drawFigure(ctx, [6, 4, 44, 56], view);
  return canvas;
}

/**
 * Build the widget once. `read()` returns the latest sheet model.
 * `writeState` and `writeOptions` persist a change.
 */
export function createSheetView({ read, writeState: persistState, writeOptions, applyRaw }) {
  ensureStyles();
  let error = null;
  function writeState(next) {
    try {
      persistState(next);
      if (error) error.textContent = "";
    } catch (exc) {
      if (error) error.textContent = exc.message || "That change was not saved.";
    }
  }
  const root = el("section", "dv-sheet");
  const body = el("div", "dv-body");
  root.setAttribute("aria-label", "Devil H3 character sheet");
  root.append(body);

  const mark = el("div", "dv-mark");
  const titles = el("div");
  titles.append(el("h1", "", "Devil H3 Sheet"), el("p", "", "Character sheet for MiniMax H3"));
  mark.append(el("div", "dv-bar"), titles);

  const preset = el("select");
  fillSelect(preset, [...Object.keys(PRESETS), "custom"].map((name) => [name, PRESET_TITLES[name]]));
  const presetField = field("Preset", preset);
  presetField.classList.add("dv-wide");

  const views = el("div", "dv-views");
  const viewButtons = new Map();
  for (const view of VIEW_ORDER) {
    const button = el("button", "dv-view");
    button.type = "button";
    button.append(miniCanvas(view), el("span", "", VIEW_TITLES[view]));
    button.addEventListener("click", () => {
      const model = read();
      if (!model.state) return;
      const selected = model.state.views.includes(view);
      if (selected && model.state.views.length === 1) {
        error.textContent = "Keep at least one view.";
        return;
      }
      const nextViews = selected
        ? model.state.views.filter((item) => item !== view)
        : [...model.state.views, view];
      writeState({ ...model.state, views: nextViews });
    });
    views.append(button);
    viewButtons.set(view, button);
  }

  const auto = el("button", "", "Auto");
  const manual = el("button", "", "Manual");
  auto.type = "button";
  manual.type = "button";
  const seg = el("div", "dv-seg");
  seg.append(auto, manual);
  auto.addEventListener("click", () => setMode("auto"));
  manual.addEventListener("click", () => setMode("manual"));

  const heightInput = el("input");
  heightInput.inputMode = "numeric";
  const widthInput = el("input");
  widthInput.inputMode = "numeric";
  const canvasHeight = el("input");
  canvasHeight.inputMode = "numeric";
  const heightChoices = el("select");
  fillSelect(heightChoices, [["", "Custom"], ...PANEL_HEIGHT_CHOICES.map((value) => [String(value), String(value)])]);
  heightChoices.addEventListener("change", () => {
    if (!heightChoices.value) return;
    heightInput.value = heightChoices.value;
    commitSize("panel_height", heightInput);
  });

  const layoutToggle = el("input");
  layoutToggle.type = "checkbox";
  const layoutLabel = el("label", "dv-check");
  layoutLabel.append(layoutToggle, el("span", "", "Pass layout image"));
  layoutToggle.addEventListener("change", () => {
    const model = read();
    writeOptions({ layoutOn: layoutToggle.checked, style: model.style });
  });

  const styleSelect = el("select");
  fillSelect(styleSelect, STYLES.map((name) => [name, STYLE_TITLES[name]]));
  styleSelect.addEventListener("change", () => {
    const model = read();
    writeOptions({ layoutOn: model.layoutOn, style: styleSelect.value });
  });

  const readout = el("div", "dv-read");
  const hint = el("p", "dv-note");
  error = el("div", "dv-error");
  error.setAttribute("role", "alert");

  const stage = el("div", "dv-stage");
  const canvas = el("canvas");
  canvas.setAttribute("aria-label", "Layout guide preview");
  stage.append(canvas);

  const noteSelect = el("select");
  fillSelect(noteSelect, NOTE_IDS.map((name) => [name, NOTE_TITLES[name]]));
  const noteInput = el("textarea");
  noteInput.placeholder = "Optional. Leave blank to follow the reference.";
  noteSelect.addEventListener("change", () => {
    const model = read();
    noteInput.value = model.state?.notes?.[noteSelect.value] || "";
  });
  noteInput.addEventListener("input", () => {
    const model = read();
    if (!model.state) return;
    const notes = { ...model.state.notes, [noteSelect.value]: noteInput.value };
    try {
      writeState({ ...model.state, notes });
      error.textContent = "";
    } catch (exc) {
      error.textContent = exc.message || "That note was not saved.";
    }
  });

  const roleSelects = ROLE_INPUTS.map((name, index) => {
    const select = el("select");
    fillSelect(select, ROLES.map((role) => [role, ROLE_TITLES[role]]));
    select.addEventListener("change", () => {
      const model = read();
      if (!model.state) return;
      writeState({
        ...model.state,
        roles: { ...model.state.roles, [name]: select.value },
      });
    });
    return field(`Reference ${index + 1}`, select);
  });

  const hands = el("select");
  fillSelect(hands, HAND_CHOICES.map((name) => [name, HAND_TITLES[name]]));
  const shape = el("select");
  fillSelect(shape, OUTFIT_SHAPES.map((name) => [name, SHAPE_TITLES[name]]));
  const footwear = el("select");
  fillSelect(footwear, FOOTWEAR_CHOICES.map((name) => [name, FOOT_TITLES[name]]));
  for (const [select, key] of [[hands, "hands"], [shape, "outfit_shape"], [footwear, "footwear"]]) {
    select.addEventListener("change", () => {
      const model = read();
      if (!model.state) return;
      writeState({ ...model.state, [key]: select.value });
    });
  }

  const raw = el("textarea");
  raw.spellcheck = false;
  raw.setAttribute("aria-label", "Sheet JSON");
  const apply = el("button", "", "Apply JSON");
  apply.type = "button";
  apply.addEventListener("click", () => {
    try {
      applyRaw(raw.value);
      error.textContent = "";
    } catch (exc) {
      error.textContent = exc.message || "That JSON was not applied.";
    }
  });
  const rawBox = el("details", "dv-block");
  const summary = el("summary", "dv-kicker", "Sheet JSON");
  rawBox.append(summary, raw, apply);

  function setMode(mode) {
    const model = read();
    if (!model.state || model.state.size.mode === mode) return;
    writeState({ ...model.state, size: { ...model.state.size, mode } });
  }

  function commitSize(key, input) {
    const model = read();
    if (!model.state) return;
    const value = Number(input.value);
    if (!Number.isInteger(value)) {
      error.textContent = "Enter a whole number of at least 32, in steps of 32.";
      return;
    }
    writeState({ ...model.state, size: { ...model.state.size, [key]: value } });
  }

  for (const [input, key] of [[heightInput, "panel_height"], [widthInput, "width"], [canvasHeight, "height"]]) {
    input.addEventListener("change", () => commitSize(key, input));
  }

  preset.addEventListener("change", () => {
    if (preset.value === "custom") return;
    const model = read();
    if (!model.state || !PRESETS[preset.value]) return;
    writeState({ ...model.state, views: [...PRESETS[preset.value]] });
  });

  const sizeRow = el("div", "dv-row");
  sizeRow.append(
    field("Sizing", seg),
    field("Panel height", heightChoices),
    field("Custom height", heightInput),
    field("Width", widthInput),
    field("Height", canvasHeight),
  );
  const optionRow = el("div", "dv-row");
  optionRow.append(layoutLabel, field("Style", styleSelect), readout);

  const notes = el("div", "dv-block");
  notes.append(el("div", "dv-kicker", "Part notes"), field("Part", noteSelect), noteInput);
  const roles = el("div", "dv-block");
  roles.append(el("div", "dv-kicker", "Reference roles"), el("div", "dv-row"));
  roles.lastChild.append(...roleSelects);
  const choices = el("div", "dv-block");
  choices.append(
    el("div", "dv-kicker", "Choices"),
    el("div", "dv-row"),
  );
  choices.lastChild.append(
    field("Hands", hands),
    field("Outfit shape", shape),
    field("Footwear", footwear),
  );

  body.append(mark, presetField, views, sizeRow, optionRow, stage, hint, error, notes, roles, choices, rawBox);

  function refresh() {
    const model = read();
    const state = model.state;
    preset.value = state ? presetName(state.views) : "custom";
    const custom = preset.querySelector('option[value="custom"]');
    if (custom) custom.disabled = true;
    for (const [view, button] of viewButtons) {
      button.classList.toggle("on", Boolean(state?.views.includes(view)));
      button.disabled = !state;
    }
    auto.classList.toggle("on", state?.size.mode === "auto");
    manual.classList.toggle("on", state?.size.mode === "manual");
    if (state && document.activeElement !== heightInput) heightInput.value = String(state.size.panel_height);
    if (state && document.activeElement !== widthInput) widthInput.value = String(state.size.width);
    if (state && document.activeElement !== canvasHeight) canvasHeight.value = String(state.size.height);
    if (state) {
      heightChoices.value = PANEL_HEIGHT_CHOICES.includes(state.size.panel_height) ? String(state.size.panel_height) : "";
    }
    const manualMode = state?.size.mode === "manual";
    widthInput.disabled = !manualMode;
    canvasHeight.disabled = !manualMode;
    heightInput.disabled = manualMode;
    heightChoices.disabled = manualMode;
    layoutToggle.checked = model.layoutOn;
    styleSelect.value = STYLES.includes(model.style) ? model.style : "none";
    if (state && document.activeElement !== noteInput) noteInput.value = state.notes[noteSelect.value] || "";
    ROLE_INPUTS.forEach((name, index) => {
      roleSelects[index].querySelector("select").value = state?.roles[name] || "same_character";
      roleSelects[index].querySelector("select").disabled = !state;
    });
    hands.value = state?.hands || "follow";
    shape.value = state?.outfit_shape || "follow";
    footwear.value = state?.footwear || "follow";
    hands.disabled = !state;
    shape.disabled = !state;
    footwear.disabled = !state;
    noteSelect.disabled = !state;
    noteInput.disabled = !state;
    if (document.activeElement !== raw) raw.value = model.raw;
    paint(canvas, model.layout);
    if (model.layout) {
      const pixels = model.layout.width * model.layout.height;
      const warn = pixels > LARGE_PIXEL_MARK ? " Large sheet." : "";
      readout.textContent = `${model.layout.width} × ${model.layout.height}${warn}`;
    } else {
      readout.textContent = "No layout";
    }
    hint.textContent = model.layoutOn
      ? "This guide is passed to H3 as layout_image (ref_image_1). Picture numbers skip empty inputs."
      : "This is the same guide either way. layout_image stays empty until Pass layout image is on.";
    error.textContent = model.error || "";
  }

  return { element: root, refresh };
}
