import os
from typing import Dict

from flask import Flask, jsonify, render_template, session


app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")

GAME_CONFIG = {
    "move_step": 1.5,
    "goal_radius": 2.5,
    "bounds": {"x": [-18.0, 18.0], "y": [-5.0, 32.0]},
    "start": {"x": 0.0, "y": 0.0},
    "goal": {"x": 10.0, "y": 24.0},
}

MOVE_DELTAS = {
    "up": (0.0, 1.0),
    "down": (0.0, -1.0),
    "left": (-1.0, 0.0),
    "right": (1.0, 0.0),
}


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def _default_state() -> Dict[str, float]:
    return {
        "x": GAME_CONFIG["start"]["x"],
        "y": GAME_CONFIG["start"]["y"],
        "won": False,
    }


def _distance_to_goal(x: float, y: float) -> float:
    goal = GAME_CONFIG["goal"]
    return ((goal["x"] - x) ** 2 + (goal["y"] - y) ** 2) ** 0.5


def _current_state() -> Dict[str, float]:
    state = session.get("game_state")
    if state is None:
        state = _default_state()
        session["game_state"] = state
    return state


def _build_response(state: Dict[str, float]) -> Dict[str, float]:
    return {
        "player": {"x": state["x"], "y": state["y"]},
        "goal": GAME_CONFIG["goal"],
        "won": state["won"],
        "distance_to_goal": round(_distance_to_goal(state["x"], state["y"]), 2),
        "bounds": GAME_CONFIG["bounds"],
        "move_step": GAME_CONFIG["move_step"],
        "goal_radius": GAME_CONFIG["goal_radius"],
    }


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/healthz")
def healthcheck():
    return jsonify({"ok": True})


@app.get("/api/state")
def game_state():
    return jsonify(_build_response(_current_state()))


@app.post("/api/reset")
def reset_game():
    state = _default_state()
    session["game_state"] = state
    return jsonify(_build_response(state))


@app.post("/api/move/<direction>")
def move_player(direction: str):
    if direction not in MOVE_DELTAS:
        return jsonify({"error": "invalid direction"}), 400

    state = _current_state()
    if state["won"]:
        return jsonify(_build_response(state))

    delta_x, delta_y = MOVE_DELTAS[direction]
    step = GAME_CONFIG["move_step"]
    min_x, max_x = GAME_CONFIG["bounds"]["x"]
    min_y, max_y = GAME_CONFIG["bounds"]["y"]

    next_x = _clamp(state["x"] + delta_x * step, min_x, max_x)
    next_y = _clamp(state["y"] + delta_y * step, min_y, max_y)

    state["x"] = next_x
    state["y"] = next_y
    state["won"] = _distance_to_goal(next_x, next_y) <= GAME_CONFIG["goal_radius"]
    session["game_state"] = state

    if state["won"]:
        print("🎉 You reached the goal!", flush=True)

    return jsonify(_build_response(state))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
