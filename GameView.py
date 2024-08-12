"""
GameView is responsible for the "world" in the simulation.

That includes:
- The camera
- Objects in the world
- Physics adherence
- Most drawing
- Termination and saving the results

All other tasks are taken care of by other code (e.g. Robot).

This is the initial code copied from an arcade demo:
https://gamedevelopment.tutsplus.com/tutorials/generate-random-cave-levels-using-cellular-automata--gamedev-9664
python3 -m arcade.examples.procedural_caves_cellular
"""

import arcade
import asyncio
import cv2
from matplotlib import pyplot as plt
import numpy as np
from pyglet.math import Vec2
import sys
import timeit

from ExplorerConfig import ExplorerConfig
from SimulationLoggers import SimLogger
from WiFi import WiFi

# Robots
import LinearSweepRobot
import NaiveRandomRobot
import PlayerCharacterRobot
import Robot
import RandomRobot

# Maps
import ImageMap
import ManualMap
import RandomMap
import WorldMap


class GameView(arcade.View):
    """ View responsible for running the simulation """

    # Setup

    def __init__(self):
        super().__init__()

        self.grid = None
        self.world_map = None
        self.robot_group_lists = []
        self.robot_list = None
        self.draw_time = 0
        self.processing_time = 0
        self.physics_engines = []
        self.timer_steps = 0
        self.bot_paths = None
        self.video = None

        self.show_stats = False
        self.quit = False

        # Special bot for camera actions and keyboard events
        self.player_sprite = None

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

        self.draw_times = []
        self.processing_times = []

    def _is_user_bot(self, robot_group_id: int) -> bool:
        """ To be overridden by users to support user defined Robot children classes """
        return False

    def _build_user_bot(self, robot_group_id: int) -> Robot.Robot:
        """ To be overridden by users to support user defined Robot children classes """
        raise NotImplementedError("_build_user_bot must be implemented if _is_user_bot can return True.")

    def _build_robot(self, robot_group_id: int) -> Robot.Robot:
        """ Call the correct constructor for the desired robot type """
        robot_type = ExplorerConfig().robot_type(robot_group_id)
        if robot_type == Robot.TYPE_NAME:
            return Robot.Robot(robot_group_id, self.world_map.sprite_list)
        elif robot_type == RandomRobot.TYPE_NAME:
            return RandomRobot.RandomRobot(robot_group_id, self.world_map.sprite_list)
        elif robot_type == NaiveRandomRobot.TYPE_NAME:
            return NaiveRandomRobot.NaiveRandomRobot(robot_group_id, self.world_map.sprite_list)
        elif robot_type == PlayerCharacterRobot.TYPE_NAME:
            if self.player_sprite is not None:
                ValueError(f"Only one player sprite allowed! Attempting to make {ExplorerConfig().bot_count(robot_group_id)}")
            self.player_sprite = PlayerCharacterRobot.PlayerCharacterRobot(robot_group_id, self.world_map.sprite_list)
            return self.player_sprite
        elif robot_type == LinearSweepRobot.TYPE_NAME:
            return LinearSweepRobot.LinearSweepRobot(robot_group_id, self.world_map.sprite_list)
        elif self._is_user_bot(robot_group_id):
            return self._build_user_bot(robot_group_id)
        raise ValueError(f"Robot type is not recognized: {robot_type}")

    def _is_user_map(self, map_type: str) -> bool:
        """ To be overridden by users to support user defined Robot children classes """
        return False

    def _build_user_map(self, map_type: str):
        """ To be overridden by users to support user defined Robot children classes """
        raise NotImplementedError("_build_user_map must be implemented if _is_user_map can return True.")

    def _build_world(self):
        """ Convert the map string to a map object """
        map_type = ExplorerConfig().map_generator_type()
        if map_type == WorldMap.TYPE_NAME:
            self.world_map = WorldMap.WorldMap()
        elif map_type == RandomMap.TYPE_NAME:
            self.world_map = RandomMap.RandomMap()
        elif map_type == ManualMap.TYPE_NAME:
            self.world_map = ManualMap.ManualMap()
        elif map_type == ImageMap.TYPE_NAME:
            self.world_map = ImageMap.ImageMap()
        elif self._is_user_map(map_type):
            self._build_user_map(map_type)
        else:
            raise ValueError(f"Unrecognized map type: {map_type}")

    def setup(self):
        """ Most values initialized here in anticipation of a simulation restart in the future. """

        self.timer_steps = 0
        self.start_time = timeit.default_timer()
        self.wifi = WiFi()
        if ExplorerConfig().save_video():
            fourcc = cv2.VideoWriter.fourcc(*'MJPG')
            self.video = cv2.VideoWriter(ExplorerConfig().output_dir() + '/robot_sim.avi', fourcc, 20, (self.window.width, self.window.height))

        # Create cave system using a 2D grid
        self._build_world()

        # Set up the bots
        self.robot_group_lists = [arcade.SpriteList(use_spatial_hash=True) for robot_group_id in range(ExplorerConfig().robot_group_count())]
        self.robot_list = arcade.SpriteList(use_spatial_hash=True)
        self.bot_paths = []
        log_str = "Bot ID to group ID and name map:\n"
        robot_ind = 0
        for robot_group_id in range(ExplorerConfig().robot_group_count()):
            for i in range(ExplorerConfig().bot_count(robot_group_id)):
                self.bot_paths.append([])
                robot_sprite = self._build_robot(robot_group_id)
                self.robot_group_lists[robot_group_id].append(robot_sprite)
                self.robot_list.append(robot_sprite)
                log_str += f"Bot {robot_ind} - Group {robot_group_id} - {robot_sprite.name}\n"
                robot_ind += 1
        SimLogger().info(log_str)

        # Setup the physics engines for collision detection and enforcement
        # Arcade's simple engine only supports acting on one sprite at a time
        for robot_sprite in self.robot_list:
            engine = arcade.PhysicsEngineSimple(robot_sprite, [self.world_map.sprite_list, self.robot_list])
            engine.update() # significantly reduces the chances of a bad initial position
            self.physics_engines.append(engine)

        # Set the screen focused on the first bot
        self.scroll_to_robot(1.0)

        # Draw info on the screen
        sprite_count = len(self.world_map.sprite_list)
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


    # Drawing

    def on_draw(self):
        """ Render the screen. """

        drawing_settings = ExplorerConfig().drawing_settings()

        draw_start_time = timeit.default_timer()

        self.clear()
        self.camera_sprites.use()

        self.world_map.draw()

        # Draw the paths over the walls and under the bots
        for robot_sprite in self.robot_list:
            if drawing_settings['draw_trajectory'] and robot_sprite.path != []:
                arcade.draw_line(robot_sprite.center_x, robot_sprite.center_y, robot_sprite.dest_x, robot_sprite.dest_y, arcade.color.BLUE, 2)
                arcade.draw_line(robot_sprite.dest_x, robot_sprite.dest_y, robot_sprite.path[0][0], robot_sprite.path[0][1], arcade.color.BLUE, 2)
                arcade.draw_line_strip(robot_sprite.path, arcade.color.BLUE, 2)

        self.robot_list.draw()

        # Draw optional bot dynamics
        for robot_sprite in self.robot_list:
            if drawing_settings['draw_sensors']:
                robot_sprite.draw_sensors()
            if drawing_settings['draw_comms']:
                robot_sprite.draw_comms()
            robot_sprite.draw_name()

        # Select the (unscrolled) camera for our GUI
        self.camera_gui.use()

        if self.show_stats:
            self.sprite_count_text.draw()

            output = f"Drawing time: {self.draw_time:.3f}"
            self.draw_time_text.text = output
            self.draw_time_text.draw()

            output = f"Processing time: {self.processing_time:.3f}"
            self.processing_time_text.text = output
            self.processing_time_text.draw()
        self.draw_times.append(self.draw_time)
        self.processing_times.append(self.processing_time)

        if ExplorerConfig().save_video():
            img = cv2.cvtColor(np.array(arcade.get_image()), cv2.COLOR_RGB2BGR)
            self.video.write(img)

        self.draw_time = timeit.default_timer() - draw_start_time

    def scroll_to_robot(self, speed: float):
        """ Scroll the window to the player.

        if CAMERA_SPEED is 1, the camera will immediately move to the desired position.
        Anything between 0 and 1 will have the camera move to the location with a smoother
        pan.
        """

        robot_sprite = self.player_sprite
        if self.player_sprite is None:
            # Rotate focus on the bots if there is no player controlled sprite
            self.bot_focus_timer += 1
            if self.bot_focus_timer >= ExplorerConfig().camera_settings()['focus_timer']:
                self.current_bot += 1
                if self.current_bot >= len(self.robot_list):
                    self.current_bot = 0
                self.bot_focus_timer = 0
            robot_sprite = self.robot_list[self.current_bot]

        # update camera position
        position = Vec2(robot_sprite.center_x - self.window.width / 2,
                        robot_sprite.center_y - self.window.height / 2)
        self.camera_sprites.move_to(position, speed)
        self.camera_sprites.update()

    def on_resize(self, width, height):
        """ Resize window

        Handle the user grabbing the edge and resizing the window.

        Note: I've never seen this working. The window size seems locked in spite of resizeable=True in the main function.
        """
        self.camera_sprites.resize(int(width), int(height))
        self.camera_gui.resize(int(width), int(height))


    # UI

    def on_key_press(self, key, modifiers):
        """ Delegate key presses to the player robot if it exists """
        if key == arcade.key.I:
            # Toggle showing stat info
            self.show_stats = not self.show_stats
        elif key == arcade.key.ESCAPE:
            # End simulation
            self.quit = True
        elif self.player_sprite is not None:
            self.player_sprite.on_key_press(key, modifiers)

    def on_key_release(self, key, modifiers):
        """ Delegate key presses to the player robot if it exists """
        if self.player_sprite is not None:
            self.player_sprite.on_key_release(key, modifiers)


    # Simulation updates

    def on_update(self, delta_time):
        """ Movement and game logic """

        # Shutdown and save results when the timer expires
        if self.quit or (ExplorerConfig().sim_steps() != 0 and self.timer_steps >= ExplorerConfig().sim_steps()):
            SimLogger().info(f"Reached end of simulation. {self.timer_steps} steps over {timeit.default_timer()-self.start_time} seconds")
            self.save_results()
            sys.exit()
        self.timer_steps += 1

        start_time = timeit.default_timer()

        # Update each robot's position

        # Async modes
        async_params = ExplorerConfig().async_params()
        async def async_robot_update():
            async with asyncio.TaskGroup() as tg:
                for i in range(len(self.robot_list)):
                    tg.create_task(self.robot_list[i].update(self.wifi))

        async def async_robot_update_with_physics():
            async with asyncio.TaskGroup() as tg:
                for i in range(len(self.robot_list)):
                    tg.create_task(self.robot_list[i].update(self.wifi, self.physics_engines[i]))

        async def sync_robot_update(a_sprite):
            await a_sprite.update(self.wifi)

        # Run the correct async version
        if async_params['use_async']:
            if async_params['async_physics']:
                asyncio.run(async_robot_update_with_physics())
            else:
                asyncio.run(async_robot_update())
                for i in range(len(self.physics_engines)):
                    hit_obstacles = self.physics_engines[i].update()
                    self.robot_list[i].handle_collision(hit_obstacles)
        else:
            for robot_sprite in self.robot_list:
                asyncio.run(sync_robot_update(robot_sprite))
            for i in range(len(self.physics_engines)):
                hit_obstacles = self.physics_engines[i].update()
                self.robot_list[i].handle_collision(hit_obstacles)

        # Store the robot positions to plot their trail later
        for i in range(len(self.robot_list)):
            self.bot_paths[i].append(self.robot_list[i].position)

        # Send messages queued up in the update
        asyncio.run(self.wifi.update(self.robot_list))

        # Update each robot's sensor
        # This isn't done in the robot update because the sensor udpate needs to know
        # about the other bots' positions.
        async def async_sensor_update():
            async with asyncio.TaskGroup() as tg:
                for robot_sprite in self.robot_list:
                    tg.create_task(robot_sprite.sensor_update([self.world_map.sprite_list, self.robot_list]))
        async def sync_sensor_update(a_sprite):
            await a_sprite.sensor_update([self.world_map.sprite_list, self.robot_list])

        if async_params['use_async']:
            asyncio.run(async_sensor_update())
        else:
            for robot_sprite in self.robot_list:
                asyncio.run(sync_sensor_update(robot_sprite))

        # Scroll the screen to the player
        self.scroll_to_robot(ExplorerConfig().camera_settings()['speed'])

        # Save the time it took to do this.
        self.processing_time = timeit.default_timer() - start_time


    # Save outputs

    def save_statistics(self):
        """ Store numeric statistics for comparing simulations """
        with open(ExplorerConfig().output_dir() + "/statistics.txt", "w+", encoding="utf-8") as f:
            seed = ExplorerConfig().map_generator_settings()['grid_seed']
            f.write(f"Random Seed: {seed}\n")
            bot_count = len(self.robot_list)
            f.write(f"Bot Count: {bot_count}\n")
            sprite_count = len(self.world_map.sprite_list) + bot_count
            f.write(f"Sprite Count: {sprite_count}\n")
            steps = self.timer_steps-1
            f.write(f"Simulation Steps: {steps}\n")

            f.write("\n")
            f.write("Note: Draw and processing times of 0 are purged.\n")
            f.write("\n")

            self.draw_times = [t for t in self.draw_times if t != 0]
            total_draw_time = 0
            for t in self.draw_times:
                total_draw_time += t
            avg_draw_time = total_draw_time / len(self.draw_times)
            f.write(f"Average Draw Time: {avg_draw_time}\n")
            f.write(f"Min Draw Time: {min(self.draw_times)}\n")
            f.write(f"Max Draw Time: {max(self.draw_times)}\n")
            f.write(f"Total Draw Time: {total_draw_time}\n")

            self.processing_times = [t for t in self.processing_times if t != 0]
            total_processing_time = 0
            for t in self.processing_times:
                total_processing_time += t
            avg_processing_time = total_processing_time / len(self.processing_times)
            f.write(f"Average Processing Time: {avg_processing_time}\n")
            f.write(f"Min Processing Time: {min(self.processing_times)}\n")
            f.write(f"Max Processing Time: {max(self.processing_times)}\n")
            f.write(f"Total Processing Time: {total_processing_time}\n")

            f.write(f"Total Simulation Time: {timeit.default_timer() - self.start_time}\n")

            f.write("\n")

            f.write(f"Draw Times: \n{self.draw_times}\n\n")
            f.write(f"Processing Times: \n{self.processing_times}\n")

    def save_results(self):
        """ Store any simulation results to files and images """

        # Save each robot's map constructed from sensor data
        for i in range(len(self.robot_list)):
            self.robot_list[i].save_map(ExplorerConfig().output_dir() + "/Map - Robot " + str(i))

        # Save the actual map and robot paths
        true_map = []
        for wall_sprite in self.world_map.sprite_list:
            true_map.append(wall_sprite.position)
        true_map = np.array(true_map).T
        fig = plt.figure()
        plt.plot(true_map[:][0], true_map[:][1], '.')
        for i in range(len(self.bot_paths)):
            new_path = np.array(self.bot_paths[i]).T
            plt.plot(new_path[:][0], new_path[:][1])
            plt.plot(self.robot_list[i].center_x, self.robot_list[i].center_y, '^')

        plt.axis((0, ExplorerConfig().max_x(), 0, ExplorerConfig().max_y()))
        plt.savefig(ExplorerConfig().output_dir() + "/true_map")
        plt.close(fig)

        if ExplorerConfig().save_video():
            self.video.release()
            cv2.destroyAllWindows()

        self.save_statistics()