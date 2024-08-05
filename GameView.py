"""
GameView is responsible for the "world" in the simulation.

That includes:
- The camera
- Objects in the world
- Physics adherence
- Most drawing
- Termination and saving the results

TODO: Move robot updates to separate processes.
TODO: Make a WiFi simulator (message passing system) so robots don't need to know about other bots

All other tasks are taken care of by other code (e.g. Robot).

This is the initial code copied from an arcade demo:
https://gamedevelopment.tutsplus.com/tutorials/generate-random-cave-levels-using-cellular-automata--gamedev-9664
python3 -m arcade.examples.procedural_caves_cellular
"""

import arcade
import timeit
from matplotlib import pyplot as plt
import numpy as np
import os
from pyglet.math import Vec2
import sys

from ExplorerConfig import ExplorerConfig
import MapMaker
from Robot import Robot


class GameView(arcade.View):
    """ View responsible for running the simulation """

    def __init__(self):
        super().__init__()

        self.grid = None
        self.grid_size = None
        self.wall_list = None
        self.robot_list = None
        self.draw_time = 0
        self.processing_time = 0
        self.physics_engines = []
        self.timer_steps = 0
        self.bot_paths = None

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

    def setup(self):
        """ Most values initialized here in anticipation of a simulation restart in the future. """
        self.timer_steps = 0

        # Create cave system using a 2D grid
        drawing_settings = ExplorerConfig().drawing_settings()
        self.grid_size = drawing_settings['scale']*drawing_settings['size']
        self.grid, self.wall_list = MapMaker.generate_map(self.grid_size, drawing_settings['scale'])
        map_generator_settings = ExplorerConfig().map_generator_settings()
        self.max_x = int(map_generator_settings['grid_width'] * self.grid_size)
        self.max_y = int(map_generator_settings['grid_height'] * self.grid_size)

        # Set up the bots
        self.robot_list = arcade.SpriteList(use_spatial_hash=True)
        self.bot_paths = []
        for i in range(ExplorerConfig().bot_count()):
            self.bot_paths.append([])
            robot_sprite = Robot(drawing_settings['scale'], self.wall_list, self.max_x, self.max_y)
            self.robot_list.append(robot_sprite)

        # Setup the physics engines for collision detection and enforcement
        # Arcade's simple engine only supports acting on one sprite at a time
        for robot_sprite in self.robot_list:
            for partner_sprite in self.robot_list:
                if partner_sprite != robot_sprite:
                    robot_sprite.add_comm_subscriber(partner_sprite)
            engine = arcade.PhysicsEngineSimple(robot_sprite, [self.wall_list, self.robot_list])
            engine.update() # significantly reduces the chances of a bad initial position
            self.physics_engines.append(engine)

        # Set the screen focused on the first bot
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

        # Draw optional bot dynamics
        drawing_settings = ExplorerConfig().drawing_settings()
        for robot_sprite in self.robot_list:
            if drawing_settings['draw_trajectory'] and robot_sprite.path != []:
                arcade.draw_line_strip(robot_sprite.path, arcade.color.BLUE, 2)
            if drawing_settings['draw_sensors']:
                robot_sprite.draw_sensors()
            if drawing_settings['draw_comms']:
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

    def scroll_to_robot(self, speed):
        """
        Scroll the window to the player.

        if CAMERA_SPEED is 1, the camera will immediately move to the desired position.
        Anything between 0 and 1 will have the camera move to the location with a smoother
        pan.
        """

        # rotate focus on the bots
        self.bot_focus_timer += 1
        if self.bot_focus_timer >= ExplorerConfig().camera_settings()['focus_timer']:
            self.current_bot += 1
            if self.current_bot >= len(self.robot_list):
                self.current_bot = 0
            self.bot_focus_timer = 0

        # update camera position
        robot_sprite = self.robot_list[self.current_bot]
        position = Vec2(robot_sprite.center_x - self.window.width / 2,
                        robot_sprite.center_y - self.window.height / 2)
        self.camera_sprites.move_to(position, speed)
        self.camera_sprites.update()

    def on_resize(self, width, height):
        """
        Resize window
        Handle the user grabbing the edge and resizing the window.

        Note: I've never seen this working. The window size seems locked in spite of resizeable=True in the main function.
        """
        self.camera_sprites.resize(int(width), int(height))
        self.camera_gui.resize(int(width), int(height))

    def save_results(self):
        """ Store any simulation results to files and images """
        # Without this, save images when the folder doesn't exist crashes
        os.makedirs("output", exist_ok=True)

        # Save each robot's map constructed from sensor data
        for i in range(len(self.robot_list)):
            self.robot_list[i].save_map("output/Map - Robot " + str(i))

        # Save the actual map and robot paths
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

        # Shutdown and save results when the timer expires
        self.timer_steps += 1
        if self.timer_steps > ExplorerConfig().sim_steps():
            self.save_results()
            sys.exit()

        start_time = timeit.default_timer()

        # Update each robot's position
        for robot_sprite in self.robot_list:
            robot_sprite.update()
        for i in range(len(self.physics_engines)):
            self.physics_engines[i].update()
            self.bot_paths[i].append(self.robot_list[i].position)

        # Update each robot's sensor
        # This isn't be done in the robot update so the robot doesn't need to know
        # about the other bots.
        for robot_sprite in self.robot_list:
            robot_sprite.sensor_update([self.wall_list, self.robot_list])

        # Scroll the screen to the player
        self.scroll_to_robot(ExplorerConfig().camera_settings()['speed'])

        # Save the time it took to do this.
        self.processing_time = timeit.default_timer() - start_time