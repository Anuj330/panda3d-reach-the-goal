from direct.gui.OnscreenText import OnscreenText
from direct.showbase.InputStateGlobal import inputState
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from panda3d.core import AmbientLight, DirectionalLight, TextNode


class ReachTheGoalGame(ShowBase):
    def __init__(self):
        super().__init__()

        self.disableMouse()

        self.move_speed = 10.0
        self.goal_radius = 2.5
        self.world_bounds = {"x": (-18.0, 18.0), "y": (-5.0, 32.0)}
        self.start_pos = (0.0, 0.0, 0.0)
        self.goal_pos = (10.0, 24.0, 1.5)
        self.goal_reached = False

        self._setup_scene()
        self._setup_lighting()
        self._setup_ui()
        self._setup_controls()
        self._setup_camera()

        # Panda3D runs this task every frame. That gives us a smooth game loop
        # without writing a manual while loop.
        self.taskMgr.add(self.update_game, "update_game")

    def _setup_scene(self):
        # "render" is the root of Panda3D's 3D scene graph.
        # Every visible object is attached to it directly or indirectly through
        # NodePaths like self.environment, self.player, and self.goal_marker.
        self.environment = self.loader.loadModel("models/environment")
        self.environment.reparentTo(self.render)
        self.environment.setScale(0.25)
        self.environment.setPos(-8, 42, 0)

        self.player = self.loader.loadModel("models/panda")
        self.player.reparentTo(self.render)
        self.player.setScale(0.005)
        self.player.setPos(*self.start_pos)
        self.player.setH(0)

        self.goal_marker = self.loader.loadModel("models/smiley")
        self.goal_marker.reparentTo(self.render)
        self.goal_marker.setScale(0.9)
        self.goal_marker.setColor(1.0, 0.85, 0.2, 1.0)
        self.goal_marker.setPos(*self.goal_pos)

    def _setup_lighting(self):
        ambient = AmbientLight("ambient")
        ambient.setColor((0.65, 0.65, 0.65, 1.0))
        self.render.setLight(self.render.attachNewNode(ambient))

        sun = DirectionalLight("sun")
        sun.setColor((0.9, 0.9, 0.85, 1.0))
        sun_np = self.render.attachNewNode(sun)
        sun_np.setHpr(-45, -35, 0)
        self.render.setLight(sun_np)

    def _setup_ui(self):
        instructions = (
            "Reach the Goal\n"
            "Move: Arrow Keys or W A S D\n"
            "Restart: R    Quit: Esc"
        )
        self.instructions_text = OnscreenText(
            text=instructions,
            parent=self.aspect2d,
            pos=(-1.28, 0.9),
            scale=0.05,
            align=TextNode.ALeft,
            fg=(1, 1, 1, 1),
            mayChange=False,
        )

        self.status_text = OnscreenText(
            text="Reach the yellow goal marker.",
            parent=self.aspect2d,
            pos=(0, -0.9),
            scale=0.06,
            align=TextNode.ACenter,
            fg=(0.95, 0.95, 0.95, 1),
            mayChange=True,
        )

    def _setup_controls(self):
        inputState.watchWithModifiers("forward", "arrow_up")
        inputState.watchWithModifiers("backward", "arrow_down")
        inputState.watchWithModifiers("left", "arrow_left")
        inputState.watchWithModifiers("right", "arrow_right")
        inputState.watchWithModifiers("forward_w", "w")
        inputState.watchWithModifiers("backward_s", "s")
        inputState.watchWithModifiers("left_a", "a")
        inputState.watchWithModifiers("right_d", "d")

        self.accept("r", self.restart_game)
        self.accept("escape", self.userExit)

    def _setup_camera(self):
        self._update_camera()

    def _is_pressed(self, *keys):
        return any(inputState.isSet(key) for key in keys)

    def _clamp_player_to_bounds(self):
        min_x, max_x = self.world_bounds["x"]
        min_y, max_y = self.world_bounds["y"]

        clamped_x = min(max(self.player.getX(), min_x), max_x)
        clamped_y = min(max(self.player.getY(), min_y), max_y)
        self.player.setPos(clamped_x, clamped_y, self.start_pos[2])

    def _update_camera(self):
        # The camera stays behind and above the player, then looks back at it
        # every frame so movement stays easy to follow.
        self.camera.setPos(
            self.player.getX(),
            self.player.getY() - 18,
            self.player.getZ() + 7,
        )
        self.camera.lookAt(self.player)

    def restart_game(self):
        self.player.setPos(*self.start_pos)
        self.goal_reached = False
        self.status_text.setText("Reach the yellow goal marker.")
        self._update_camera()

    def update_game(self, task):
        if self.goal_reached:
            self._update_camera()
            return Task.cont

        dt = globalClock.getDt()
        move_x = 0.0
        move_y = 0.0

        # Movement is calculated each frame from the current key state.
        # That makes motion smooth while the player holds a key down.
        if self._is_pressed("left", "left_a"):
            move_x -= self.move_speed * dt
        if self._is_pressed("right", "right_d"):
            move_x += self.move_speed * dt
        if self._is_pressed("forward", "forward_w"):
            move_y += self.move_speed * dt
        if self._is_pressed("backward", "backward_s"):
            move_y -= self.move_speed * dt

        self.player.setX(self.player.getX() + move_x)
        self.player.setY(self.player.getY() + move_y)
        self._clamp_player_to_bounds()

        if move_x < 0:
            self.player.setH(90)
        elif move_x > 0:
            self.player.setH(-90)
        elif move_y > 0:
            self.player.setH(0)
        elif move_y < 0:
            self.player.setH(180)

        position = self.player.getPos()
        print(
            f"Player position: x={position.x:.2f}, y={position.y:.2f}, z={position.z:.2f}",
            end="\r",
            flush=True,
        )

        # Goal logic: when the player is close enough to the goal marker,
        # the game prints a success message and stops the update task.
        if (self.player.getPos() - self.goal_marker.getPos()).length() <= self.goal_radius:
            self.goal_reached = True
            self.status_text.setText("You win! Press R to play again.")
            print("\n🎉 You reached the goal!")
            self._update_camera()
            return Task.cont

        self._update_camera()
        return Task.cont


if __name__ == "__main__":
    game = ReachTheGoalGame()
    game.run()
