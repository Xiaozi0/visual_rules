#!/usr/bin/env python3
"""Serve an interactive browser game for the SpongeBob-style rolling cube."""

from __future__ import annotations

import argparse
import http.server
import socketserver
from pathlib import Path


HTML = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Rolling Cube Orientation Game</title>
  <style>
    :root {
      --bg: #f1eee6;
      --ink: #222;
      --muted: #666;
      --panel: #ffffff;
      --line: #c7c0b5;
      --blue: #2b73c8;
      --red: #e64b3f;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--ink);
      background: var(--bg);
    }
    main {
      display: grid;
      grid-template-columns: minmax(620px, 1fr) 330px;
      min-height: 100vh;
      gap: 18px;
      padding: 18px;
    }
    #stage {
      width: 100%;
      height: calc(100vh - 36px);
      min-height: 620px;
      background: #ebe7dd;
      border: 1px solid var(--line);
      display: block;
    }
    aside {
      background: var(--panel);
      border: 1px solid var(--line);
      padding: 16px;
      min-height: 620px;
    }
    h1 {
      margin: 0 0 12px;
      font-size: 22px;
      line-height: 1.15;
    }
    .goal {
      border: 2px solid var(--red);
      padding: 10px;
      margin: 12px 0;
      font-size: 15px;
      background: #fff7f6;
    }
    .status {
      min-height: 30px;
      font-weight: 700;
      color: #154f85;
      margin: 8px 0 12px;
    }
    .row {
      border-top: 1px solid #e0d9ce;
      padding: 10px 0;
      font-size: 14px;
      line-height: 1.45;
    }
    .label {
      display: block;
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      margin-bottom: 4px;
    }
    .controls {
      display: grid;
      grid-template-columns: repeat(3, 64px);
      gap: 7px;
      justify-content: center;
      margin: 16px 0;
    }
    button {
      border: 1px solid #9b9489;
      background: #f8f7f2;
      color: var(--ink);
      min-height: 42px;
      font-size: 18px;
      cursor: pointer;
    }
    button:hover { background: #ece7dc; }
    .wide {
      width: 100%;
      margin: 4px 0;
      font-size: 14px;
    }
    .legend {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
      margin-top: 8px;
    }
    .chip {
      display: flex;
      align-items: center;
      gap: 7px;
      font-size: 13px;
    }
    .swatch {
      width: 20px;
      height: 20px;
      border: 1px solid #333;
      flex: 0 0 auto;
    }
    @media (max-width: 900px) {
      main { grid-template-columns: 1fr; }
      #stage { height: 62vh; min-height: 480px; }
      aside { min-height: 0; }
    }
  </style>
</head>
<body>
<main>
  <canvas id="stage"></canvas>
  <aside>
    <h1>Rolling Cube Orientation Game</h1>
    <div class="goal" id="goal"></div>
    <div class="status" id="status"></div>

    <div class="row"><span class="label">Current Position</span><span id="position"></span></div>
    <div class="row"><span class="label">Visible Faces</span><span id="visible"></span></div>
    <div class="row"><span class="label">Hidden / Other Faces</span><span id="hidden"></span></div>
    <div class="row"><span class="label">Move History</span><span id="moves"></span></div>

    <div class="controls">
      <span></span><button id="north">↑</button><span></span>
      <button id="west">←</button><button id="south">↓</button><button id="east">→</button>
    </div>
    <button class="wide" id="undo">Undo</button>
    <button class="wide" id="reset">Reset</button>
    <button class="wide" id="new">New Puzzle</button>

    <div class="row">
      <span class="label">Face Legend</span>
      <div class="legend" id="legend"></div>
    </div>
  </aside>
</main>

<script>
const faces = {
  face: { label: "Face", color: "#f4d84d" },
  pants: { label: "Pants", color: "#9b4f12" },
  shirt: { label: "Shirt", color: "#ffffff" },
  back: { label: "Back", color: "#d8cb51" },
  left: { label: "Left side", color: "#f0ce43" },
  right: { label: "Right side", color: "#e7c73e" }
};

const moveLabel = { N: "north", S: "south", W: "west", E: "east" };
const delta = { N: [-1, 0], S: [1, 0], W: [0, -1], E: [0, 1] };

function defaultState(row, col) {
  return {
    row, col,
    o: {
      top: "face",
      bottom: "shirt",
      north: "back",
      south: "pants",
      west: "left",
      east: "right"
    }
  };
}

function cloneState(s) {
  return { row: s.row, col: s.col, o: { ...s.o } };
}

function roll(state, move) {
  const o = state.o;
  let n;
  if (move === "N") {
    n = { top: o.south, bottom: o.north, north: o.top, south: o.bottom, west: o.west, east: o.east };
  } else if (move === "S") {
    n = { top: o.north, bottom: o.south, north: o.bottom, south: o.top, west: o.west, east: o.east };
  } else if (move === "W") {
    n = { top: o.east, bottom: o.west, north: o.north, south: o.south, west: o.top, east: o.bottom };
  } else {
    n = { top: o.west, bottom: o.east, north: o.north, south: o.south, west: o.bottom, east: o.top };
  }
  return { row: state.row + delta[move][0], col: state.col + delta[move][1], o: n };
}

function applyMoves(start, moves) {
  let s = cloneState(start);
  for (const m of moves) s = roll(s, m);
  return s;
}

function legalMovesFrom(row, col) {
  return Object.keys(delta).filter(m => {
    const [dr, dc] = delta[m];
    const nr = row + dr, nc = col + dc;
    return nr >= 0 && nr < game.rows && nc >= 0 && nc < game.cols;
  });
}

function randomChoice(xs) {
  return xs[Math.floor(Math.random() * xs.length)];
}

const game = {
  rows: 4,
  cols: 4,
  start: defaultState(2, 2),
  state: defaultState(2, 2),
  history: [],
  moves: [],
  goalCell: [0, 0],
  goalTop: "face"
};

function newPuzzle() {
  game.start = defaultState(Math.floor(game.rows / 2), Math.floor(game.cols / 2));
  game.state = cloneState(game.start);
  game.history = [];
  game.moves = [];

  let row = game.start.row, col = game.start.col;
  const solution = [];
  for (let i = 0; i < 4; i++) {
    const m = randomChoice(legalMovesFrom(row, col));
    solution.push(m);
    row += delta[m][0];
    col += delta[m][1];
  }
  const final = applyMoves(game.start, solution);
  game.goalCell = [final.row, final.col];
  game.goalTop = final.o.top;
  setStatus("New puzzle.");
  draw();
}

function inside(s) {
  return s.row >= 0 && s.row < game.rows && s.col >= 0 && s.col < game.cols;
}

function doMove(m) {
  const next = roll(game.state, m);
  if (!inside(next)) {
    setStatus("Illegal move: the cube would leave the board.");
    draw();
    return;
  }
  game.history.push(cloneState(game.state));
  game.moves.push(m);
  game.state = next;
  setStatus(isWon() ? "Solved." : `Rolled ${moveLabel[m]}.`);
  draw();
}

function undo() {
  if (!game.history.length) return;
  game.state = game.history.pop();
  game.moves.pop();
  setStatus("Undid one move.");
  draw();
}

function reset() {
  game.state = cloneState(game.start);
  game.history = [];
  game.moves = [];
  setStatus("Reset to start.");
  draw();
}

function isWon() {
  return game.state.row === game.goalCell[0] && game.state.col === game.goalCell[1] && game.state.o.top === game.goalTop;
}

function setStatus(text) {
  document.getElementById("status").textContent = `Status: ${text}`;
}

const canvas = document.getElementById("stage");
const ctx = canvas.getContext("2d");

function resizeCanvas() {
  const rect = canvas.getBoundingClientRect();
  const dpr = window.devicePixelRatio || 1;
  canvas.width = Math.floor(rect.width * dpr);
  canvas.height = Math.floor(rect.height * dpr);
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  draw();
}

function draw() {
  const rect = canvas.getBoundingClientRect();
  const w = rect.width, h = rect.height;
  ctx.clearRect(0, 0, w, h);
  ctx.fillStyle = "#ebe7dd";
  ctx.fillRect(0, 0, w, h);
  ctx.fillStyle = "#222";
  ctx.font = "700 20px system-ui";
  ctx.textAlign = "center";
  ctx.fillText("Move the cube to the red cell with the required top face", w / 2, 34);

  const tileW = Math.min((w - 160) / game.cols, 128);
  const tileH = tileW * 0.52;
  const cubeH = tileW * 0.68;
  const origin = {
    x: w / 2 - ((game.cols - game.rows) * tileW) / 4,
    y: 96
  };

  for (let r = 0; r < game.rows; r++) {
    for (let c = 0; c < game.cols; c++) {
      drawIsoCell(origin, tileW, tileH, r, c, (r + c) % 2 === 0 ? "#f7f7f2" : "#303234");
      if (r === game.goalCell[0] && c === game.goalCell[1]) {
        const corners = isoCellCorners(origin, tileW, tileH, r, c, 0);
        ctx.strokeStyle = "#e64b3f";
        ctx.lineWidth = 5;
        strokePolygon(insetPolygon(corners, 0.12));
        const center = centroid(corners);
        ctx.fillStyle = "#e64b3f";
        ctx.font = "700 12px system-ui";
        ctx.textAlign = "center";
        ctx.fillText("GOAL", center[0], center[1] + 10);
      }
    }
  }

  drawIsoCube(origin, tileW, tileH, cubeH, game.state);
  drawLegend(36, h - 42);
  updatePanel();
}

function polygon(points, fill) {
  ctx.beginPath();
  ctx.moveTo(points[0][0], points[0][1]);
  for (const p of points.slice(1)) ctx.lineTo(p[0], p[1]);
  ctx.closePath();
  ctx.fillStyle = fill;
  ctx.fill();
  ctx.strokeStyle = "#151515";
  ctx.lineWidth = 3;
  ctx.stroke();
}

function isoProject(origin, tileW, tileH, row, col, z = 0, cubeH = 0) {
  return [
    origin.x + (col - row) * tileW / 2,
    origin.y + (col + row) * tileH / 2 - z * cubeH
  ];
}

function isoCellCorners(origin, tileW, tileH, row, col, z = 0, cubeH = 0) {
  return [
    isoProject(origin, tileW, tileH, row, col, z, cubeH),
    isoProject(origin, tileW, tileH, row, col + 1, z, cubeH),
    isoProject(origin, tileW, tileH, row + 1, col + 1, z, cubeH),
    isoProject(origin, tileW, tileH, row + 1, col, z, cubeH)
  ];
}

function drawIsoCell(origin, tileW, tileH, row, col, fill) {
  const corners = isoCellCorners(origin, tileW, tileH, row, col, 0);
  polygon(corners, fill);
  ctx.strokeStyle = "#777";
  ctx.lineWidth = 1.5;
  strokePolygon(corners);
}

function drawIsoCube(origin, tileW, tileH, cubeH, state) {
  const bottom = isoCellCorners(origin, tileW, tileH, state.row, state.col, 0, cubeH);
  const top = isoCellCorners(origin, tileW, tileH, state.row, state.col, 1, cubeH);
  const eastFace = [top[1], top[2], bottom[2], bottom[1]];
  const southFace = [top[3], top[2], bottom[2], bottom[3]];

  ctx.fillStyle = "rgba(0,0,0,0.25)";
  ctx.beginPath();
  ctx.moveTo(bottom[0][0] + 8, bottom[0][1] + 8);
  for (const p of bottom.slice(1)) ctx.lineTo(p[0] + 8, p[1] + 8);
  ctx.closePath();
  ctx.fill();

  polygon(southFace, shade(faces[state.o.south].color, -10));
  mark(southFace, state.o.south);
  polygon(eastFace, shade(faces[state.o.east].color, -4));
  mark(eastFace, state.o.east);
  polygon(top, faces[state.o.top].color);
  mark(top, state.o.top);
}

function strokePolygon(points) {
  ctx.beginPath();
  ctx.moveTo(points[0][0], points[0][1]);
  for (const p of points.slice(1)) ctx.lineTo(p[0], p[1]);
  ctx.closePath();
  ctx.stroke();
}

function insetPolygon(points, amount) {
  const center = centroid(points);
  return points.map(p => [
    p[0] + (center[0] - p[0]) * amount,
    p[1] + (center[1] - p[1]) * amount
  ]);
}

function shade(hex, percent) {
  const n = parseInt(hex.slice(1), 16);
  const amt = Math.round(2.55 * percent);
  const r = Math.max(0, Math.min(255, (n >> 16) + amt));
  const g = Math.max(0, Math.min(255, ((n >> 8) & 255) + amt));
  const b = Math.max(0, Math.min(255, (n & 255) + amt));
  return `#${(1 << 24 | r << 16 | g << 8 | b).toString(16).slice(1)}`;
}

function centroid(points) {
  return [
    points.reduce((s, p) => s + p[0], 0) / points.length,
    points.reduce((s, p) => s + p[1], 0) / points.length
  ];
}

function mark(points, face) {
  const [cx, cy] = centroid(points);
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  if (face === "face") {
    ctx.fillStyle = "#fff";
    ctx.strokeStyle = "#222";
    ctx.lineWidth = 1.5;
    ctx.beginPath(); ctx.ellipse(cx - 14, cy - 8, 7, 5, 0, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
    ctx.beginPath(); ctx.ellipse(cx + 14, cy - 8, 7, 5, 0, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
    ctx.fillStyle = "#1c6aa6";
    ctx.beginPath(); ctx.arc(cx - 14, cy - 8, 2.5, 0, Math.PI * 2); ctx.fill();
    ctx.beginPath(); ctx.arc(cx + 14, cy - 8, 2.5, 0, Math.PI * 2); ctx.fill();
    ctx.strokeStyle = "#222";
    ctx.lineWidth = 2;
    ctx.beginPath(); ctx.arc(cx, cy + 3, 17, 0.15 * Math.PI, 0.85 * Math.PI); ctx.stroke();
    ctx.fillStyle = "#111";
    ctx.font = "700 12px system-ui";
    ctx.fillText("Face", cx, cy + 29);
  } else if (face === "pants") {
    ctx.fillStyle = "#7c3c0d";
    ctx.fillRect(cx - 28, cy - 9, 56, 22);
    ctx.strokeStyle = "#222";
    ctx.setLineDash([4, 3]);
    ctx.beginPath(); ctx.moveTo(cx - 28, cy + 1); ctx.lineTo(cx + 28, cy + 1); ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = "#111";
    ctx.font = "700 12px system-ui";
    ctx.fillText("Pants", cx, cy + 30);
  } else if (face === "shirt") {
    ctx.fillStyle = "#fff";
    ctx.fillRect(cx - 28, cy - 11, 56, 24);
    ctx.strokeStyle = "#333";
    ctx.strokeRect(cx - 28, cy - 11, 56, 24);
    ctx.fillStyle = "#d63232";
    ctx.beginPath();
    ctx.moveTo(cx - 7, cy - 8); ctx.lineTo(cx, cy + 6); ctx.lineTo(cx + 7, cy - 8); ctx.closePath(); ctx.fill();
    ctx.fillStyle = "#111";
    ctx.font = "700 12px system-ui";
    ctx.fillText("Shirt", cx, cy + 30);
  } else {
    ctx.fillStyle = "#111";
    ctx.font = "700 12px system-ui";
    ctx.fillText(faces[face].label, cx, cy);
  }
}

function drawTopFaceMark(x, y, size, face) {
  const cx = x + size / 2;
  const cy = y + size / 2;
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";

  if (face === "face") {
    ctx.fillStyle = "#fff";
    ctx.strokeStyle = "#222";
    ctx.lineWidth = 2;
    ctx.beginPath(); ctx.ellipse(cx - size * 0.18, cy - size * 0.12, size * 0.09, size * 0.07, 0, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
    ctx.beginPath(); ctx.ellipse(cx + size * 0.18, cy - size * 0.12, size * 0.09, size * 0.07, 0, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
    ctx.fillStyle = "#1c6aa6";
    ctx.beginPath(); ctx.arc(cx - size * 0.18, cy - size * 0.12, size * 0.035, 0, Math.PI * 2); ctx.fill();
    ctx.beginPath(); ctx.arc(cx + size * 0.18, cy - size * 0.12, size * 0.035, 0, Math.PI * 2); ctx.fill();
    ctx.strokeStyle = "#222";
    ctx.lineWidth = 3;
    ctx.beginPath(); ctx.arc(cx, cy + size * 0.02, size * 0.22, 0.15 * Math.PI, 0.85 * Math.PI); ctx.stroke();
    ctx.fillStyle = "#111";
    ctx.font = "700 15px system-ui";
    ctx.fillText("Face", cx, cy + size * 0.32);
  } else if (face === "pants") {
    ctx.fillStyle = "#7c3c0d";
    ctx.fillRect(x + size * 0.18, y + size * 0.36, size * 0.64, size * 0.24);
    ctx.strokeStyle = "#222";
    ctx.setLineDash([5, 4]);
    ctx.beginPath(); ctx.moveTo(x + size * 0.18, y + size * 0.48); ctx.lineTo(x + size * 0.82, y + size * 0.48); ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = "#111";
    ctx.font = "700 15px system-ui";
    ctx.fillText("Pants", cx, y + size * 0.74);
  } else if (face === "shirt") {
    ctx.fillStyle = "#fff";
    ctx.fillRect(x + size * 0.18, y + size * 0.33, size * 0.64, size * 0.28);
    ctx.strokeStyle = "#333";
    ctx.lineWidth = 2;
    ctx.strokeRect(x + size * 0.18, y + size * 0.33, size * 0.64, size * 0.28);
    ctx.fillStyle = "#d63232";
    ctx.beginPath();
    ctx.moveTo(cx - size * 0.08, y + size * 0.35);
    ctx.lineTo(cx, y + size * 0.56);
    ctx.lineTo(cx + size * 0.08, y + size * 0.35);
    ctx.closePath();
    ctx.fill();
    ctx.fillStyle = "#111";
    ctx.font = "700 15px system-ui";
    ctx.fillText("Shirt", cx, y + size * 0.74);
  } else {
    ctx.fillStyle = "#111";
    ctx.font = "700 15px system-ui";
    ctx.fillText(faces[face].label, cx, cy);
  }
}

function drawLegend(x, y) {
  ctx.fillStyle = "#222";
  ctx.font = "700 14px system-ui";
  ctx.textAlign = "left";
  ctx.fillText("Face legend:", x, y);
  let lx = x + 110;
  for (const key of ["face", "pants", "shirt", "back", "left", "right"]) {
    ctx.fillStyle = faces[key].color;
    ctx.fillRect(lx, y - 12, 18, 18);
    ctx.strokeStyle = "#333";
    ctx.strokeRect(lx, y - 12, 18, 18);
    ctx.fillStyle = "#222";
    ctx.font = "12px system-ui";
    ctx.fillText(faces[key].label, lx + 24, y + 2);
    lx += 98;
  }
}

function updatePanel() {
  document.getElementById("goal").textContent =
    `Goal: reach red cell (${game.goalCell[0]}, ${game.goalCell[1]}) with top face = ${faces[game.goalTop].label}.`;
  document.getElementById("position").textContent = `row ${game.state.row}, col ${game.state.col}`;
  document.getElementById("visible").textContent =
    `top=${faces[game.state.o.top].label}, front=${faces[game.state.o.south].label}, right=${faces[game.state.o.east].label}`;
  document.getElementById("hidden").textContent =
    `bottom=${faces[game.state.o.bottom].label}, back=${faces[game.state.o.north].label}, left=${faces[game.state.o.west].label}`;
  document.getElementById("moves").textContent =
    game.moves.length ? game.moves.map(m => moveLabel[m]).join(" → ") : "(none)";
  if (isWon()) setStatus("Solved.");
}

document.getElementById("north").onclick = () => doMove("N");
document.getElementById("south").onclick = () => doMove("S");
document.getElementById("west").onclick = () => doMove("W");
document.getElementById("east").onclick = () => doMove("E");
document.getElementById("undo").onclick = undo;
document.getElementById("reset").onclick = reset;
document.getElementById("new").onclick = newPuzzle;

document.addEventListener("keydown", e => {
  const map = { ArrowUp: "N", w: "N", W: "N", ArrowDown: "S", s: "S", S: "S",
                ArrowLeft: "W", a: "W", A: "W", ArrowRight: "E", d: "E", D: "E" };
  if (map[e.key]) {
    e.preventDefault();
    doMove(map[e.key]);
  }
});

const legend = document.getElementById("legend");
for (const key of ["face", "pants", "shirt", "back", "left", "right"]) {
  const item = document.createElement("div");
  item.className = "chip";
  item.innerHTML = `<span class="swatch" style="background:${faces[key].color}"></span><span>${faces[key].label}</span>`;
  legend.appendChild(item);
}

window.addEventListener("resize", resizeCanvas);
newPuzzle();
resizeCanvas();
</script>
</body>
</html>
"""


class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path in {"/", "/index.html"}:
            encoded = HTML.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)
            return
        self.send_error(404, "Not found")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    with socketserver.TCPServer((args.host, args.port), Handler) as server:
        url = f"http://{args.host}:{args.port}"
        print(f"Serving Rolling Cube Orientation Game at {url}")
        print("Press Ctrl+C to stop.")
        server.serve_forever()


if __name__ == "__main__":
    main()
