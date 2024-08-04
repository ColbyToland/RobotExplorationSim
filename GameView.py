"""
This is the initial code copied from an arcade demo (original comment below) with tweaked parameters.

---

This example procedurally develops a random cave based on cellular automata.

For more information, see:
https://gamedevelopment.tutsplus.com/tutorials/generate-random-cave-levels-using-cellular-automata--gamedev-9664

If Python and Arcade are installed, this example can be run from the command line with:
python -m arcade.examples.procedural_caves_cellular
"""

import arcade
import timeit
from matplotlib import pyplot as plt
import numpy as np
import os
from pyglet.math import Vec2
import sys

import MapMaker
from Robot import Robot

# Sprite scaling. Make this larger, like 0.5 to zoom in and add
# 'mystery' to what you can see. Make it smaller, like 0.1 to see
# more of the map.
SPRITE_SCALING = 0.125
SPRITE_SIZE = 128 * SPRITE_SCALING

# How close the player can get to the edge before we scroll.
VIEWPORT_MARGIN = 300

# How fast the camera pans to the player. 1.0 is instant.
CAMERA_SPEED = 0.1
FOCUS_TIMER = 200

BOT_COUNT = 3
END_STEPS = 1000

DRAW_TRAJECTORY = True
DRAW_SENSORS = True
DRAW_COMMS = True

class GameView(arcade.View):
    """
    Main application class.
    """

    def __init__(self):
        super().__init__()

        self.grid = None
        self.wall_list = None
        self.robot_list = None
        self.draw_time = 0
        self.processing_time = 0
        self.physics_engines = []
        self.timer_steps = 0

        # Create the cameras. One for the GUI, one for the sprites.
        # We scroll the 'sprite world' but not the GUI.
        self.camera_sprites = arcade.Camera(self.window.width, self.window.height)
        self.camera_gui = arcade.Camera(self.window.width, self.window.height)
        self.current_bot = 0
        self.bot_focus_timer = 0

        arcade.set_background_color(arcade.color.BLACK)

        self.sprite_count_text = None
        self.draw_time_text = None
        self.processing_time_text = None

        self.bot_paths = None

    def setup(self):
        self.timer_steps = 0

        self.robot_list = arcade.SpriteList(use_spatial_hash=True)

        # Create cave system using a 2D grid
        self.grid, self.wall_list = MapMaker.generate_map(SPRITE_SIZE, SPRITE_SCALING)
        self.max_x = int(MapMaker.GRID_WIDTH * SPRITE_SIZE)
        self.max_y = int(MapMaker.GRID_HEIGHT * SPRITE_SIZE)

        # Set up the player
        self.bot_paths = []
        for i in range(BOT_COUNT):
            self.bot_paths.append([])
            robot_sprite = Robot(SPRITE_SCALING, self.wall_list, self.max_x, self.max_y)
            robot_sprite.enable_comms(wireless_range=5*SPRITE_SIZE, update_period=10)
            self.robot_list.append(robot_sprite)

        # need a a completed robot list before setting up the engines
        for robot_sprite in self.robot_list:
            for partner_sprite in self.robot_list:
                if partner_sprite != robot_sprite:
                    robot_sprite.add_comm_subscriber(partner_sprite)
            engine = arcade.PhysicsEngineSimple(robot_sprite, [self.wall_list, self.robot_list])
            engine.update() # significantly reduces the chances of a bad initial position
            self.physics_engines.append(engine)

        self.scroll_to_robot(1.0)

        # Draw info on the screen
        sprite_count = len(self.wall_list)
        output = f"Sprite Count: {sprite_count:,}"
        self.sprite_count_text = arcade.Text(output,
                                             20,
                                             self.window.height - 20,
                                             arcade.color.WHITE, 16)

        output = "Drawing time:"
        self.draw_time_text = arcade.Text(output,
                                          20,
                                          self.window.height - 40,
                                          arcade.color.WHITE, 16)

        output = "Processing time:"
        self.processing_time_text = arcade.Text(output,
                                                20,
                                                self.window.height - 60,
                                                arcade.color.WHITE, 16)

    def on_draw(self):
        """ Render the screen. """

        # Start timing how long this takes
        draw_start_time = timeit.default_timer()

        # This command should happen before we start drawing. It will clear
        # the screen to the background color, and erase what we drew last frame.
        self.clear()

        # Select the camera we'll use to draw all our sprites
        self.camera_sprites.use()

        # Draw the sprites
        self.wall_list.draw()
        self.robot_list.draw()
        for robot_sprite in self.robot_list:
            if DRAW_TRAJECTORY and robot_sprite.path != []:
                arcade.draw_line_strip(robot_sprite.path, arcade.color.BLUE, 2)
            if DRAW_SENSORS:
                robot_sprite.draw_sensors()
            if DRAW_COMMS:
                robot_sprite.draw_comms()

        # Select the (unscrolled) camera for our GUI
        self.camera_gui.use()

        self.sprite_count_text.draw()
        output = f"Drawing time: {self.draw_time:.3f}"
        self.draw_time_text.text = output
        self.draw_time_text.draw()

        output = f"Processing time: {self.processing_time:.3f}"
        self.processing_time_text.text = output
        self.processing_time_text.draw()

        self.draw_time = timeit.default_timer() - draw_start_time

    def scroll_to_robot(self, speed=CAMERA_SPEED):
        """
        Scroll the window to the player.

        if CAMERA_SPEED is 1, the camera will immediately move to the desired position.
        Anything between 0 and 1 will have the camera move to the location with a smoother
        pan.
        """

        # rotate focus on the bots
        self.bot_focus_timer += 1
        if self.bot_focus_timer >= FOCUS_TIMER:
            self.current_bot += 1
            if self.current_bot >= BOT_COUNT:
                self.current_bot = 0
            self.bot_focus_timer = 0

        robot_sprite = self.robot_list[self.current_bot]
        position = Vec2(robot_sprite.center_x - self.window.width / 2,
                        robot_sprite.center_y - self.window.height / 2)
        self.camera_sprites.move_to(position, speed)
        self.camera_sprites.update()

    def on_resize(self, width, height):
        """
        Resize window
        Handle the user grabbing the edge and resizing the window.
        """
        self.camera_sprites.resize(int(width), int(height))
        self.camera_gui.resize(int(width), int(height))

    def save_results(self):
        os.makedirs("output", exist_ok=True)

        for i in range(len(self.robot_list)):
            self.robot_list[i].save_map("output/Map - Robot " + str(i))

        true_map = []
        for wall_sprite in self.wall_list:
            true_map.append(wall_sprite.position)
        true_map = np.array(true_map).T
        fig = plt.figure()
        plt.plot(true_map[:][0], true_map[:][1], '.')
        for i in range(len(self.bot_paths)):
            new_path = np.array(self.bot_paths[i]).T
            plt.plot(new_path[:][0], new_path[:][1])
            plt.plot(self.robot_list[i].center_x, self.robot_list[i].center_y, '^')
        plt.axis((0, self.max_x, 0, self.max_y))
        plt.savefig("output/true_map")

    def on_update(self, delta_time):
        """ Movement and game logic """

        self.timer_steps += 1
        if self.timer_steps > END_STEPS:
            self.save_results()
            sys.exit()

        start_time = timeit.default_timer()

        # Call update on all sprites (The sprites don't do much in this
        # example though.)
        for robot_sprite in self.robot_list:
            robot_sprite.update()
        for i in range(len(self.physics_engines)):
            self.physics_engines[i].update()
            self.bot_paths[i].append(self.robot_list[i].position)

        # sensor updates
        for robot_sprite in self.robot_list:
            robot_sprite.sensor_update([self.wall_list, self.robot_list])

        # Scroll the screen to the player
        self.scroll_to_robot()

        # Save the time it took to do this.
        self.processing_time = timeit.default_timer() - start_time