/**
 * Line-figure plans in a 0..1000 box. The same numbers live in py/figures.py.
 * Heads are ovals, torsos are rectangles, red dots are joints.
 * Outfit plans have no head.
 */

export const VIEW_LABELS = {
  "face_front": "front bust",
  "face_left": "left-profile bust",
  "face_right": "right-profile bust",
  "face_3q_left": "left three-quarter bust",
  "face_3q_right": "right three-quarter bust",
  "face_back": "rear bust",
  "body_front": "front full body",
  "body_left": "left-profile full body",
  "body_back": "rear full body",
  "clothing_front": "flat outfit front",
  "clothing_back": "flat outfit back",
  "hands": "both hands",
  "feet": "both feet"
};

export const PLANS = {"face_front": [["oval", 500, 280, 160, 180], ["line", 500, 460, 500, 540], ["rect", 250, 540, 500, 280], ["rect", 410, 320, 40, 24], ["rect", 550, 320, 40, 24], ["dot", 280, 580], ["dot", 720, 580]], "face_left": [["oval", 420, 300, 140, 180], ["line", 540, 300, 820, 340], ["rect", 300, 560, 360, 260], ["rect", 470, 330, 30, 20], ["dot", 360, 600]], "face_right": [["oval", 580, 300, 140, 180], ["line", 460, 300, 180, 340], ["rect", 340, 560, 360, 260], ["rect", 500, 330, 30, 20], ["dot", 640, 600]], "face_3q_left": [["oval", 460, 290, 150, 180], ["line", 560, 310, 760, 350], ["rect", 280, 550, 420, 270], ["rect", 430, 330, 28, 20], ["rect", 520, 345, 18, 14], ["dot", 320, 590], ["dot", 660, 590]], "face_3q_right": [["oval", 540, 290, 150, 180], ["line", 440, 310, 240, 350], ["rect", 300, 550, 420, 270], ["rect", 500, 330, 28, 20], ["rect", 430, 345, 18, 14], ["dot", 340, 590], ["dot", 680, 590]], "face_back": [["fill", 340, 120, 320, 140], ["oval", 500, 300, 160, 180], ["rect", 250, 540, 500, 280], ["line", 500, 200, 500, 700], ["dot", 280, 580], ["dot", 720, 580]], "body_front": [["oval", 500, 120, 90, 100], ["line", 500, 220, 500, 270], ["rect", 340, 270, 320, 260], ["line", 340, 310, 150, 490], ["line", 660, 310, 850, 490], ["line", 430, 530, 380, 880], ["line", 570, 530, 620, 880], ["rect", 300, 870, 150, 60], ["rect", 560, 870, 150, 60], ["rect", 445, 145, 28, 16], ["rect", 530, 145, 28, 16], ["dot", 340, 310], ["dot", 660, 310], ["dot", 430, 530], ["dot", 570, 530]], "body_left": [["oval", 430, 120, 78, 100], ["line", 500, 125, 690, 145], ["line", 470, 220, 470, 270], ["rect", 390, 270, 170, 260], ["line", 470, 320, 620, 500], ["line", 470, 530, 520, 880], ["rect", 450, 870, 170, 55], ["rect", 455, 140, 22, 14], ["dot", 470, 320], ["dot", 470, 530]], "body_back": [["fill", 400, 30, 200, 90], ["oval", 500, 130, 90, 100], ["line", 500, 230, 500, 520], ["rect", 340, 270, 320, 260], ["line", 340, 310, 160, 490], ["line", 660, 310, 840, 490], ["line", 430, 530, 380, 880], ["line", 570, 530, 620, 880], ["rect", 300, 870, 150, 60], ["rect", 560, 870, 150, 60], ["dot", 340, 310], ["dot", 660, 310]], "clothing_front": [["rect", 420, 80, 160, 70], ["rect", 300, 140, 400, 620], ["rect", 80, 160, 220, 180], ["rect", 700, 160, 220, 180], ["rect", 470, 280, 24, 24], ["rect", 470, 360, 24, 24], ["rect", 470, 440, 24, 24], ["line", 300, 760, 700, 760]], "clothing_back": [["rect", 420, 80, 160, 70], ["rect", 300, 140, 400, 620], ["rect", 80, 160, 220, 180], ["rect", 700, 160, 220, 180], ["line", 500, 150, 500, 740], ["line", 300, 760, 700, 760]], "hands": [["rect", 80, 280, 280, 340], ["rect", 90, 120, 50, 170], ["rect", 155, 80, 50, 210], ["rect", 220, 90, 50, 200], ["rect", 285, 150, 46, 150], ["rect", 620, 280, 280, 340], ["rect", 640, 150, 46, 150], ["rect", 710, 90, 50, 200], ["rect", 775, 80, 50, 210], ["rect", 840, 120, 50, 170], ["dot", 200, 400], ["dot", 780, 400]], "feet": [["rect", 80, 360, 340, 220], ["rect", 80, 300, 120, 80], ["rect", 560, 360, 340, 220], ["rect", 780, 300, 120, 80], ["line", 80, 540, 420, 540], ["line", 560, 540, 900, 540], ["dot", 200, 420], ["dot", 760, 420]]};

export function figurePlan(viewId) {
  return PLANS[viewId];
}

export function drawFigure(ctx, box, viewId) {
  const plan = PLANS[viewId];
  if (!plan) return;
  const [x, y, w, h] = box;
  const sx = (value) => x + (value / 1000) * w;
  const sy = (value) => y + (value / 1000) * h;
  const span = Math.min(w, h);
  ctx.save();
  ctx.lineWidth = Math.max(1, span * 0.012);
  ctx.lineJoin = "miter";
  ctx.lineCap = "butt";
  ctx.strokeStyle = "#5a504c";
  ctx.fillStyle = "#5a504c";
  for (const op of plan) {
    const kind = op[0];
    if (kind === "line") {
      ctx.beginPath();
      ctx.moveTo(sx(op[1]), sy(op[2]));
      ctx.lineTo(sx(op[3]), sy(op[4]));
      ctx.stroke();
    } else if (kind === "rect" || kind === "fill") {
      const rx = sx(op[1]);
      const ry = sy(op[2]);
      const rw = (op[3] / 1000) * w;
      const rh = (op[4] / 1000) * h;
      if (kind === "fill") ctx.fillRect(rx, ry, rw, rh);
      else ctx.strokeRect(rx, ry, rw, rh);
    } else if (kind === "oval") {
      ctx.beginPath();
      ctx.ellipse(sx(op[1]), sy(op[2]), Math.max(1, (op[3] / 1000) * w), Math.max(1, (op[4] / 1000) * h), 0, 0, Math.PI * 2);
      ctx.stroke();
    } else if (kind === "dot") {
      const radius = Math.max(2, span * 0.02);
      ctx.fillStyle = "#e25b45";
      ctx.fillRect(sx(op[1]) - radius, sy(op[2]) - radius, radius * 2, radius * 2);
      ctx.fillStyle = "#5a504c";
    }
  }
  ctx.restore();
}
