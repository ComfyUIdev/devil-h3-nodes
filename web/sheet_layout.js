/**
 * Sheet placement. Keep the arithmetic in step with py/layout.py:
 * rational math, half-up pixels, a 4px edge, then optional body widening.
 */

import { VIEW_LABELS } from "./sheet_figures.js";

const BODIES = ["body_front", "body_left", "body_back"];
const CLOTHES = ["clothing_front", "clothing_back"];
const DETAILS = ["hands", "feet"];
const HEADS = ["face_front", "face_left", "face_right", "face_3q_left", "face_3q_right", "face_back"];
const LEGACY = ["face_front", "face_left", "body_front", "body_left", "body_back", "hands", "feet"];
const SEVEN = LEGACY;

class Frac {
  constructor(n, d = 1n) {
    let numer = BigInt(n);
    let denom = BigInt(d);
    if (denom < 0n) {
      numer = -numer;
      denom = -denom;
    }
    const g = gcd(numer < 0n ? -numer : numer, denom);
    this.n = numer / g;
    this.d = denom / g;
  }

  add(other) {
    return new Frac(this.n * other.d + other.n * this.d, this.d * other.d);
  }

  sub(other) {
    return new Frac(this.n * other.d - other.n * this.d, this.d * other.d);
  }

  mul(other) {
    return new Frac(this.n * other.n, this.d * other.d);
  }

  div(other) {
    return new Frac(this.n * other.d, this.d * other.n);
  }
}

function gcd(a, b) {
  let x = a;
  let y = b;
  while (y !== 0n) {
    const next = x % y;
    x = y;
    y = next;
  }
  return x;
}

const F = (n, d = 1) => new Frac(n, d);

function round6(value) {
  const rounded = (2n * value.n * 1000000n + value.d) / (2n * value.d);
  return Number(rounded) / 1000000;
}

function ceil32(value) {
  const step = 32n * value.d;
  return Number(((value.n + step - 1n) / step) * 32n);
}

function halfUp(value) {
  return Number((2n * value.n + value.d) / (2n * value.d));
}

function minFrac(a, b) {
  return a.n * b.d <= b.n * a.d ? a : b;
}

function ideal(views, panelHeight) {
  const height = F(panelHeight);
  const pad = height.div(F(18));
  const gap = height.div(F(30));
  const bodyW = height.mul(F(2)).div(F(5));
  const auxW = height.div(F(2));
  const selected = new Set(views);
  const subset = [...selected].every((view) => LEGACY.includes(view));
  const fullSeven = selected.size === SEVEN.length && SEVEN.every((view) => selected.has(view));
  const legacy = subset && !fullSeven;
  const boxes = new Map();
  let x = pad;
  const y = pad;
  if (legacy) {
    const portraits = ["face_front", "face_left"].filter((view) => selected.has(view));
    const details = DETAILS.filter((view) => selected.has(view));
    const bodies = BODIES.filter((view) => selected.has(view));
    if (portraits.length || details.length) {
      const columns = portraits.length ? portraits.length : 1;
      const groupW = auxW.mul(F(columns)).add(gap.mul(F(columns - 1)));
      if (portraits.length) {
        const portraitH = details.length ? height.mul(F(3)).div(F(5)) : height;
        portraits.forEach((view, index) => {
          boxes.set(view, [x.add(auxW.add(gap).mul(F(index))), y, auxW, portraitH]);
        });
        if (details.length) {
          const bandY = y.add(portraitH).add(gap);
          const bandH = height.sub(portraitH).sub(gap);
          const bandW = details.length === 2 ? groupW.sub(gap).div(F(2)) : groupW;
          details.forEach((view, index) => {
            boxes.set(view, [x.add(bandW.add(gap).mul(F(index))), bandY, bandW, bandH]);
          });
        }
      } else if (details.length === 2) {
        const bandH = height.sub(gap).div(F(2));
        details.forEach((view, index) => {
          boxes.set(view, [x, y.add(bandH.add(gap).mul(F(index))), auxW, bandH]);
        });
      } else {
        boxes.set(details[0], [x, y, auxW, height]);
      }
      x = x.add(groupW).add(gap);
    }
    for (const view of bodies) {
      boxes.set(view, [x, y, bodyW, height]);
      x = x.add(bodyW).add(gap);
    }
  } else {
    const portraits = HEADS.filter((view) => selected.has(view));
    const bodies = BODIES.filter((view) => selected.has(view));
    const clothes = CLOTHES.filter((view) => selected.has(view));
    const details = DETAILS.filter((view) => selected.has(view));
    const stacked = selected.size === SEVEN.length && SEVEN.every((view) => selected.has(view));
    if (portraits.length) {
      const cols = stacked ? 1 : Math.min(2, portraits.length);
      const rows = Math.ceil(portraits.length / cols);
      const cellH = height.sub(gap.mul(F(rows - 1))).div(F(rows));
      portraits.forEach((view, index) => {
        const col = index % cols;
        const row = Math.floor(index / cols);
        boxes.set(view, [
          x.add(auxW.add(gap).mul(F(col))),
          y.add(cellH.add(gap).mul(F(row))),
          auxW,
          cellH,
        ]);
      });
      x = x.add(auxW.mul(F(cols))).add(gap.mul(F(cols - 1))).add(gap);
    }
    for (const view of [...bodies, ...clothes]) {
      boxes.set(view, [x, y, bodyW, height]);
      x = x.add(bodyW).add(gap);
    }
    if (details.length) {
      const cellH = height.sub(gap.mul(F(details.length - 1))).div(F(details.length));
      details.forEach((view, index) => {
        boxes.set(view, [x, y.add(cellH.add(gap).mul(F(index))), auxW, cellH]);
      });
      x = x.add(auxW).add(gap);
    }
  }
  const idealW = x.sub(gap).add(pad);
  const idealH = height.add(pad).add(pad);
  return { boxes, idealW, idealH };
}

function pixelBoxes(boxes, scale, ox, oy, width, height) {
  const placed = [];
  for (const [view, box] of boxes) {
    const [left, top, boxW, boxH] = box;
    let x0 = halfUp(left.mul(scale).add(ox));
    let y0 = halfUp(top.mul(scale).add(oy));
    let x1 = halfUp(left.add(boxW).mul(scale).add(ox));
    let y1 = halfUp(top.add(boxH).mul(scale).add(oy));
    x0 = Math.max(0, Math.min(width - 1, x0));
    y0 = Math.max(0, Math.min(height - 1, y0));
    x1 = Math.max(x0 + 1, Math.min(width, x1));
    y1 = Math.max(y0 + 1, Math.min(height, y1));
    placed.push({ id: view, box: [x0, y0, x1, y1] });
  }
  return placed;
}

function tighten(placed, width, height) {
  const edge = 4;
  const gutter = 8;
  const original = placed.map((item) => item.box.slice());
  placed.forEach((item, index) => {
    const [left, top, right, bottom] = original[index];
    let x0 = edge;
    let y0 = edge;
    let x1 = width - edge;
    let y1 = height - edge;
    original.forEach((other, otherIndex) => {
      if (otherIndex === index) return;
      const [ol, ot, oright, ob] = other;
      if (oright <= left) x0 = Math.max(x0, Math.floor((oright + left) / 2) + Math.floor(gutter / 2));
      if (ol >= right) x1 = Math.min(x1, Math.floor((right + ol) / 2) - Math.floor(gutter / 2));
      if (ob <= top) y0 = Math.max(y0, Math.floor((ob + top) / 2) + Math.floor(gutter / 2));
      if (ot >= bottom) y1 = Math.min(y1, Math.floor((bottom + ot) / 2) - Math.floor(gutter / 2));
    });
    item.box = x1 - x0 < 8 || y1 - y0 < 8 ? [left, top, right, bottom] : [x0, y0, x1, y1];
  });
  return placed;
}

function framePx(width, height) {
  return Math.max(2, Math.floor((Math.min(width, height) + 96) / 192));
}

function widenBodies(placed, width, height, panelHeight) {
  const bodies = placed.filter((item) => BODIES.includes(item.id));
  if (!bodies.length) return { placed, width };
  const frame = framePx(width, height);
  let needed = Math.floor((panelHeight * 21 + 50 - 1) / 50);
  needed += 2 * frame + 2;
  const grows = bodies.map((item) => Math.max(0, needed - (item.box[2] - item.box[0])));
  const extra = grows.reduce((sum, grow) => sum + grow, 0);
  if (extra <= 0) return { placed, width };
  const newWidth = Math.floor((width + extra + 31) / 32) * 32;
  const slack = newWidth - width - extra;
  const share = Math.floor(slack / grows.length);
  const remain = slack % grows.length;
  const grown = grows.map((grow, index) => grow + share + (index < remain ? 1 : 0));
  const edges = bodies.map((item, index) => [item.box[0], item.box[2], grown[index]]);
  const own = new Map(bodies.map((item, index) => [item.id, grown[index]]));
  for (const item of placed) {
    const [left, top, right, bottom] = item.box;
    const shift = edges.reduce((sum, [, edgeR, grow]) => sum + (edgeR <= left + 1 ? grow : 0), 0);
    const grow = own.get(item.id) || 0;
    item.box = [left + shift, top, right + shift + grow, bottom];
  }
  return { placed, width: newWidth };
}

function normalize(placed, width, height) {
  return placed.map((item) => {
    const [left, top, right, bottom] = item.box;
    return {
      id: item.id,
      rect: [
        round6(F(left, width)),
        round6(F(top, height)),
        round6(F(right - left, width)),
        round6(F(bottom - top, height)),
      ],
      label: VIEW_LABELS[item.id],
    };
  });
}

export function planSheet(state, limit = 16384) {
  const { boxes, idealW, idealH } = ideal(state.views, state.size.panel_height);
  let width;
  let height;
  let scale;
  if (state.size.mode === "auto") {
    width = ceil32(idealW);
    height = ceil32(idealH);
    scale = F(1);
  } else {
    width = state.size.width;
    height = state.size.height;
    scale = minFrac(F(width).div(idealW), F(height).div(idealH));
  }
  const ox = F(width).sub(idealW.mul(scale)).div(F(2));
  const oy = F(height).sub(idealH.mul(scale)).div(F(2));
  let placed = pixelBoxes(boxes, scale, ox, oy, width, height);
  const order = new Map(state.views.map((view, index) => [view, index]));
  placed.sort((a, b) => order.get(a.id) - order.get(b.id));
  placed = tighten(placed, width, height);
  if (state.size.mode === "auto") {
    const widened = widenBodies(placed, width, height, state.size.panel_height);
    placed = widened.placed;
    width = widened.width;
  }
  if (width > limit || height > limit) {
    const error = new Error("limit");
    error.code = "limit";
    throw error;
  }
  const bodies = placed.filter((item) => BODIES.includes(item.id));
  const feetY = bodies.length ? round6(F(Math.min(...bodies.map((item) => item.box[3])), height)) : null;
  return { width, height, panels: normalize(placed, width, height), feetY };
}
