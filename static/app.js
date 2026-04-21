const canvas = document.getElementById("game-canvas");
const context = canvas.getContext("2d");
const statusEl = document.getElementById("status");
const positionEl = document.getElementById("position");
const distanceEl = document.getElementById("distance");
const restartButton = document.getElementById("restart-button");

const pressedDirections = new Set();
const keyMap = {
  ArrowUp: "up",
  ArrowDown: "down",
  ArrowLeft: "left",
  ArrowRight: "right",
  w: "up",
  a: "left",
  s: "down",
  d: "right",
};

let gameState = null;
let lastMoveAt = 0;
const moveIntervalMs = 110;

function worldToCanvas(x, y) {
  const bounds = gameState.bounds;
  const xRange = bounds.x[1] - bounds.x[0];
  const yRange = bounds.y[1] - bounds.y[0];
  const px = ((x - bounds.x[0]) / xRange) * canvas.width;
  const py = canvas.height - ((y - bounds.y[0]) / yRange) * canvas.height;
  return { x: px, y: py };
}

function updateHud() {
  const { player, won, distance_to_goal: distance } = gameState;
  positionEl.textContent = `Position: x=${player.x.toFixed(1)}, y=${player.y.toFixed(1)}`;
  distanceEl.textContent = `Distance to goal: ${distance.toFixed(1)}`;
  statusEl.textContent = won ? "🎉 You reached the goal!" : "Use the keyboard to reach the goal.";
}

function drawBoard() {
  if (!gameState) {
    return;
  }

  context.clearRect(0, 0, canvas.width, canvas.height);

  const goal = worldToCanvas(gameState.goal.x, gameState.goal.y);
  const player = worldToCanvas(gameState.player.x, gameState.player.y);
  const bounds = gameState.bounds;
  const goalRadius = (gameState.goal_radius / (bounds.x[1] - bounds.x[0])) * canvas.width;

  context.save();
  context.fillStyle = "rgba(255, 255, 255, 0.05)";
  for (let x = 0; x < canvas.width; x += 32) {
    context.fillRect(x, 0, 1, canvas.height);
  }
  for (let y = 0; y < canvas.height; y += 32) {
    context.fillRect(0, y, canvas.width, 1);
  }
  context.restore();

  context.beginPath();
  context.fillStyle = "rgba(255, 213, 79, 0.18)";
  context.arc(goal.x, goal.y, goalRadius, 0, Math.PI * 2);
  context.fill();

  context.beginPath();
  context.fillStyle = "#ffd54f";
  context.arc(goal.x, goal.y, 16, 0, Math.PI * 2);
  context.fill();

  context.fillStyle = "#173449";
  context.font = "700 16px Trebuchet MS";
  context.textAlign = "center";
  context.fillText("GOAL", goal.x, goal.y + 5);

  context.beginPath();
  context.fillStyle = "#79d2ff";
  context.arc(player.x, player.y, 14, 0, Math.PI * 2);
  context.fill();

  context.fillStyle = "#10212f";
  context.font = "700 14px Trebuchet MS";
  context.fillText("P", player.x, player.y + 5);
}

async function callJson(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }

  return response.json();
}

async function syncState() {
  gameState = await callJson("/api/state");
  updateHud();
  drawBoard();
}

async function move(direction) {
  if (!gameState || gameState.won) {
    return;
  }

  gameState = await callJson(`/api/move/${direction}`, { method: "POST" });
  updateHud();
  drawBoard();
}

function activeDirection() {
  const priority = ["up", "down", "left", "right"];
  return priority.find((direction) => pressedDirections.has(direction));
}

function tick(timestamp) {
  if (gameState && !gameState.won) {
    const direction = activeDirection();
    if (direction && timestamp - lastMoveAt >= moveIntervalMs) {
      lastMoveAt = timestamp;
      move(direction).catch((error) => {
        statusEl.textContent = `Error: ${error.message}`;
      });
    }
  }

  requestAnimationFrame(tick);
}

window.addEventListener("keydown", async (event) => {
  const key = event.key.length === 1 ? event.key.toLowerCase() : event.key;
  const direction = keyMap[key];

  if (direction) {
    event.preventDefault();
    pressedDirections.add(direction);
  }

  if (key === "r") {
    event.preventDefault();
    gameState = await callJson("/api/reset", { method: "POST" });
    updateHud();
    drawBoard();
  }
});

window.addEventListener("keyup", (event) => {
  const key = event.key.length === 1 ? event.key.toLowerCase() : event.key;
  const direction = keyMap[key];
  if (direction) {
    pressedDirections.delete(direction);
  }
});

restartButton.addEventListener("click", async () => {
  gameState = await callJson("/api/reset", { method: "POST" });
  updateHud();
  drawBoard();
});

syncState()
  .then(() => requestAnimationFrame(tick))
  .catch((error) => {
    statusEl.textContent = `Error: ${error.message}`;
  });
