/**
 * ComfyUI entry for Devil H3 Character Sheet.
 * The DOM widget edits state_json. Layout math stays in the browser,
 * so the preview does not call the server.
 */

import { app } from "../../scripts/app.js";
import { parseState, serializeState } from "./sheet_state.js";
import { planSheet } from "./sheet_layout.js";
import { createSheetView } from "./sheet_ui.js";

const NODE = "DevilH3CharacterSheet";

function widget(node, name) {
  return node.widgets?.find((item) => item.name === name);
}

function hideWidget(item) {
  if (!item) return;
  item.hidden = true;
  item.computeSize = () => [0, -4];
  const element = item.element || item.inputEl;
  if (element) element.style.display = "none";
}

function readModel(node) {
  const raw = String(widget(node, "state_json")?.value ?? "");
  const layoutOn = widget(node, "use_layout_image")?.value === true;
  const style = widget(node, "style")?.value || "none";
  try {
    const state = parseState(raw);
    return { raw, state, layout: planSheet(state), layoutOn, style, error: "" };
  } catch (exc) {
    return { raw, state: null, layout: null, layoutOn, style, error: exc.message || "Invalid sheet." };
  }
}

function withHistory(node, change) {
  const canvas = node.graph?.list_of_graphcanvas?.[0] || app.canvas;
  canvas?.emitBeforeChange?.();
  try {
    change();
  } finally {
    canvas?.emitAfterChange?.();
  }
  node.setDirtyCanvas?.(true, true);
}

function attach(node) {
  if (node.devilH3Sheet) return;
  const stateWidget = widget(node, "state_json");
  if (!stateWidget || typeof node.addDOMWidget !== "function" || typeof document === "undefined") return;
  node.devilH3Sheet = true;
  node.color = "#e25b45";
  node.bgcolor = "#1c1412";
  node.boxcolor = "#e6ff3a";

  const view = createSheetView({
    read: () => readModel(node),
    writeState: (next) => {
      const text = serializeState(parseState(serializeState(next)));
      withHistory(node, () => {
        stateWidget.value = text;
        stateWidget.callback?.(text);
      });
      view.refresh();
    },
    writeOptions: ({ layoutOn, style }) => {
      const layoutWidget = widget(node, "use_layout_image");
      const styleWidget = widget(node, "style");
      withHistory(node, () => {
        if (layoutWidget) {
          layoutWidget.value = layoutOn;
          layoutWidget.callback?.(layoutOn);
        }
        if (styleWidget) {
          styleWidget.value = style;
          styleWidget.callback?.(style);
        }
      });
      view.refresh();
    },
    applyRaw: (text) => {
      const clean = serializeState(parseState(text));
      withHistory(node, () => {
        stateWidget.value = clean;
        stateWidget.callback?.(clean);
      });
      view.refresh();
    },
  });

  const dom = node.addDOMWidget("devil_h3_sheet", "devil_h3_sheet", view.element, {
    serialize: false,
    hideOnZoom: false,
    getValue() {
      return "";
    },
    setValue() {},
  });
  dom.serialize = false;
  dom.computeSize = (width) => [width, 720];
  hideWidget(stateWidget);
  hideWidget(widget(node, "use_layout_image"));
  hideWidget(widget(node, "style"));

  const previousConfigure = node.onConfigure;
  node.onConfigure = function (...args) {
    const result = previousConfigure?.apply(this, args);
    view.refresh();
    return result;
  };
  if (node.size?.[0] < 880) node.setSize?.([960, 860]);
  view.refresh();
}

app.registerExtension({
  name: "devil-h3-nodes.DevilH3CharacterSheet",
  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (nodeData?.name !== NODE) return;
    const previous = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function (...args) {
      const result = previous?.apply(this, args);
      attach(this);
      return result;
    };
  },
});
