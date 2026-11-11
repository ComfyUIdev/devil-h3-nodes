/**
 * ComfyUI entry for Devil H3 Character Sheet.
 * The DOM widget edits state_json. Layout math stays in the browser,
 * so the preview does not call the server.
 */

import { app } from "../../scripts/app.js";
import { parseState, serializeState } from "./sheet_state.js";
import { planSheet } from "./sheet_layout.js";
import { createSheetView } from "./sheet_ui.js";
import {
  NODE_OPEN_WIDTH,
  WIDGET_MAX_HEIGHT,
  estimateSheetHeight,
  openedNodeSize,
  sheetFrame,
  shouldFitNewNode,
} from "./sheet_metrics.js";

const NODE = "DevilH3CharacterSheet";
const WIDGET_NAME = "devil_h3_sheet";

function widget(node, name) {
  return node.widgets?.find((item) => item.name === name);
}

function hideWidget(item) {
  if (!item) return;
  item.hidden = true;
  item.options = item.options || {};
  item.options.hidden = true;
  item.computeSize = () => [0, -4];
  item.computeLayoutSize = () => ({ minHeight: 0, maxHeight: 0, minWidth: 0 });
  const element = item.element || item.inputEl;
  if (element) element.style.display = "none";
}

function nodeWidth(node) {
  const sized = Number(node?.size?.[0]);
  return sized > 80 ? sized : NODE_OPEN_WIDTH;
}

function frameFor(node) {
  const views = readModel(node).state?.views?.length || 5;
  return sheetFrame(estimateSheetHeight(views, nodeWidth(node)));
}

function vueHost(root) {
  return root.closest?.(".lg-node") || null;
}

/**
 * Both renderers size the slot from addDOMWidget (getMinHeight / getHeight /
 * computeSize). This only fixes the box the slot is mounted in.
 * Vue nodes shrink the column to the card. The classic overlay is already
 * positioned and scaled by the canvas, so its ancestors stay untouched.
 */
function stretchSheet(root, node) {
  if (!root) return;
  root.style.boxSizing = "border-box";
  root.style.minWidth = "0";
  root.style.alignSelf = "stretch";
  root.style.justifySelf = "stretch";
  const host = vueHost(root);
  if (!host) {
    root.style.setProperty("width", "100%", "important");
    root.style.setProperty("height", "100%", "important");
    root.style.setProperty("max-width", "100%", "important");
    root.style.setProperty("max-height", "100%", "important");
    return;
  }
  const grid = host.querySelector?.("[data-testid='node-widgets'], .lg-node-widgets");
  if (grid) {
    grid.style.setProperty("box-sizing", "border-box", "important");
    grid.style.setProperty("width", "100%", "important");
    grid.style.setProperty("max-width", "100%", "important");
    grid.style.setProperty("min-width", "0", "important");
    grid.style.setProperty("align-self", "stretch", "important");
    grid.style.setProperty("justify-self", "stretch", "important");
    grid.style.setProperty("grid-template-columns", "minmax(0, 1fr)", "important");
    if (grid.querySelectorAll(":scope > *").length <= 1) {
      grid.style.setProperty("grid-template-rows", "minmax(0, 1fr)", "important");
    }
  }
  const declared = parseFloat(getComputedStyle(host).getPropertyValue("--node-width"));
  const pixelWidth = declared > 80 ? Math.max(200, declared - 20) : Math.max(280, nodeWidth(node) - 24);
  root.style.setProperty("width", `${pixelWidth}px`, "important");
  root.style.setProperty("max-width", "none", "important");
  root.style.setProperty("height", "100%", "important");
  let el = root.parentElement;
  while (el && el !== host) {
    el.style.setProperty("box-sizing", "border-box", "important");
    el.style.setProperty("width", "100%", "important");
    el.style.setProperty("max-width", "100%", "important");
    el.style.setProperty("min-width", "0", "important");
    el.style.setProperty("align-self", "stretch", "important");
    el.style.setProperty("justify-self", "stretch", "important");
    el = el.parentElement;
  }
}

function syncCollapsed(node, root) {
  if (!root) return;
  root.style.display = node.flags?.collapsed ? "none" : "";
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

  const layoutPass = { run() {} };
  const view = createSheetView({
    read: () => readModel(node),
    writeState: (next) => {
      const text = serializeState(parseState(serializeState(next)));
      withHistory(node, () => {
        stateWidget.value = text;
        stateWidget.callback?.(text);
      });
      layoutPass.run();
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
      layoutPass.run();
    },
    applyRaw: (text) => {
      const clean = serializeState(parseState(text));
      withHistory(node, () => {
        stateWidget.value = clean;
        stateWidget.callback?.(clean);
      });
      layoutPass.run();
    },
  });

  let frameHeight = frameFor(node).height;
  function syncFrame() {
    syncCollapsed(node, view.element);
    stretchSheet(view.element, node);
    const measured = view.element.querySelector(".dv-body")?.scrollHeight || 0;
    const estimated = estimateSheetHeight(readModel(node).state?.views?.length || 5, nodeWidth(node));
    const content = measured > 120 ? measured : estimated;
    frameHeight = sheetFrame(content).height;
    view.element.style.setProperty("--comfy-widget-min-height", `${frameHeight}px`);
    view.element.style.setProperty("--comfy-widget-height", `${frameHeight}px`);
    view.element.style.setProperty("--comfy-widget-max-height", `${WIDGET_MAX_HEIGHT}px`);
  }
  layoutPass.run = () => {
    syncFrame();
    view.refresh();
  };

  const dom = node.addDOMWidget(WIDGET_NAME, WIDGET_NAME, view.element, {
    serialize: false,
    hideOnZoom: false,
    getValue() {
      return "";
    },
    setValue() {},
    getMinHeight() {
      return node.flags?.collapsed ? 0 : frameHeight;
    },
    getHeight() {
      return node.flags?.collapsed ? 0 : frameHeight;
    },
    getMaxHeight() {
      return node.flags?.collapsed ? 0 : WIDGET_MAX_HEIGHT;
    },
    afterResize() {
      layoutPass.run();
    },
  });
  dom.serialize = false;
  if (dom.options) dom.options.serialize = false;
  dom.computeLayoutSize = () => ({
    minHeight: node.flags?.collapsed ? 0 : frameHeight,
    maxHeight: node.flags?.collapsed ? 0 : WIDGET_MAX_HEIGHT,
    minWidth: 0,
  });
  dom.computeSize = (width) => [Math.max(width || nodeWidth(node), 0), node.flags?.collapsed ? 0 : frameHeight];
  hideWidget(stateWidget);
  hideWidget(widget(node, "use_layout_image"));
  hideWidget(widget(node, "style"));

  let keepSavedSize = false;
  const previousConfigure = node.onConfigure;
  node.onConfigure = function (...args) {
    keepSavedSize = true;
    const result = previousConfigure?.apply(this, args);
    layoutPass.run();
    return result;
  };
  const previousResize = node.onResize;
  node.onResize = function (...args) {
    const result = previousResize?.apply(this, args);
    layoutPass.run();
    return result;
  };

  function fitNewNode() {
    if (keepSavedSize || node.flags?.collapsed) return;
    if (!shouldFitNewNode(node.size) && (node.size?.[0] || 0) >= NODE_OPEN_WIDTH) return;
    node.setSize?.(openedNodeSize(frameHeight));
  }

  fitNewNode();
  layoutPass.run();
  requestAnimationFrame(() => {
    const host = view.element.closest?.(".lg-node");
    if (host && typeof ResizeObserver !== "undefined") {
      let last = host.clientWidth;
      const observer = new ResizeObserver(() => {
        const next = host.clientWidth;
        if (Math.abs(next - last) < 2) return;
        last = next;
        layoutPass.run();
      });
      observer.observe(host);
      const previousRemoved = node.onRemoved;
      node.onRemoved = function (...args) {
        observer.disconnect();
        return previousRemoved?.apply(this, args);
      };
    }
    layoutPass.run();
    fitNewNode();
  });
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
