/**
 * How tall the sheet widget asks the node to be.
 * The view cards use a CSS grid of CARD_MIN_PX tracks, so a wider node
 * is shorter: the same cards share rows instead of stacking.
 */

export const CARD_MIN_PX = 96;
export const CARD_GAP_PX = 6;
export const NODE_OPEN_WIDTH = 560;
export const WIDGET_MAX_HEIGHT = 720;
export const VIEW_GRID_COLUMNS = `repeat(auto-fill, minmax(${CARD_MIN_PX}px, 1fr))`;

export function columnsForWidth(width) {
  const inner = Math.max(CARD_MIN_PX, width - 24);
  return Math.max(1, Math.floor((inner + CARD_GAP_PX) / (CARD_MIN_PX + CARD_GAP_PX)));
}

export function estimateSheetHeight(viewCount, width) {
  const count = Math.max(1, viewCount || 1);
  const rows = Math.ceil(count / columnsForWidth(width));
  const cards = rows * 104;
  // Header, preset, size, options, guide, notes, roles, choices, JSON row.
  const chrome = 48 + 52 + 58 + 36 + 292 + 168 + 92 + 76 + 32;
  return cards + chrome;
}

export function sheetFrame(contentHeight, maxHeight = WIDGET_MAX_HEIGHT) {
  const raw = Math.max(160, Math.ceil(Number(contentHeight) || 0));
  const height = Math.min(raw, maxHeight);
  return { height, scroll: raw > maxHeight, maxHeight };
}
