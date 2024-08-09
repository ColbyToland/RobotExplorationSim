"""
The base robot doesn't move but provides the core functionality.

Responsibilities:
- Build an occupancy map
- Manage sensors
- Path planning and movement
- Communicate with other bots
"""

import arcade
import asyncio
from datetime import datetime
import math
import random

from ExplorerConfig import ExplorerConfig
from LaserRangeFinder import LaserRangeFinder
from RobotMessages import OccupancyGridMessage
from OccupancyGrid import OccupancyGrid
from OccupancyGridTypes import GridCellStatus
from SimulationLoggers import RobotLogger, setup_robot_logger
from types import FunctionType
from typing import Optional
from utils import fTuplePt2, manhattan_dist, PtType
import WiFi


TYPE_NAME = "base"


# Store the assigned robot names in a global to avoid duplicates
assigned_robot_names = []

class Robot(arcade.Sprite):
    """ Sprite to simulate a single robot """

    ## Setup ##

    def __init__(self, 
                 robot_group_id: int, 
                 wall_list: arcade.SpriteList, 
                 speed: float=5, 
                 img_fname: str=":resources:images/animated_characters/robot/robot_idle.png"):
        """ Initialization takes care of all setup. There are no additional setup functions. """

        drawing_settings = ExplorerConfig().drawing_settings()
        super().__init__(img_fname, drawing_settings['scale'])

        self.logger_id = setup_robot_logger()
        self._robot_group_id = robot_group_id
        self.timer_steps= 0
        self.name = None
        self.gen_name()
        self.wall_list = wall_list
        self.max_x = ExplorerConfig().max_x()
        self.max_y = ExplorerConfig().max_y()
        self.grid_size = ExplorerConfig().grid_size()
        self.center_x, self.center_y = self._get_valid_position()
        self.dest_x, self.dest_y = self.center_x, self.center_y
        self.speed = speed

        self.nametext = arcade.Text(self.name,
                                    self.center_x,
                                    self.center_y - self.grid_size / 2,
                                    arcade.color.WHITE, 8)

        # path planning
        self.barrier_list = arcade.AStarBarrierList(self, self.wall_list, self.grid_size, 0, self.max_x, 0, self.max_y)
        self.path = []
        self.replan_on_collision = True

        self.jam_check = {'position_buffer': [], 'index':0}
        for i in range(10):
            self.jam_check['position_buffer'].append([self.center_x + i*self.speed, self.center_y + i*self.speed])

        # sensors
        robot_sensor_settings = ExplorerConfig().robot_sensor_settings(self._robot_group_id)
        self.laser_width = robot_sensor_settings['beam_grid_scale']*self.grid_size + 1 # +1 to avoid potential problems with exactly 1 grid width
        self.range_finders = []
        max_range = robot_sensor_settings['range_grid_scale']*self.grid_size
        for i in range(robot_sensor_settings['count']):
            self.range_finders.append(LaserRangeFinder(self, 
                                                       self.laser_width, 
                                                       max_range=max_range,
                                                       orientation=i*2*math.pi/robot_sensor_settings['count']))

        # map
        self.map = OccupancyGrid(ExplorerConfig().robot_map_resolution(self._robot_group_id))
        self.partner_maps = {}

        # comms
        robot_comm_settings = ExplorerConfig().robot_comm_settings(self._robot_group_id)
        self.comm_enabled = True
        self.comm_range = robot_comm_settings['wireless_range_grid_scale']*self.grid_size
        self.comm_update_period = robot_comm_settings['update_period']

    @property
    def robot_group_id(self):
        return self._robot_group_id

    def gen_name(self):
        """ Randomly generate a unique name from name part lists """
        global assigned_robot_names
        name_parts = ExplorerConfig().robot_name_gen_parameters(self._robot_group_id)
        while not self.name:
            candidate = ""
            for name_part_list in name_parts:
                if candidate != "":
                    candidate += " "
                candidate += random.choice(name_part_list)
            if candidate not in assigned_robot_names:
                self.name = candidate
                assigned_robot_names.append(self.name)
        RobotLogger(self.logger_id).info("Robot name: " + self.name)


    def enable_comms(self):
        """ Turn on comms """
        self.comm_enabled = True

    def disable_comms(self):
        """ Turn off comms """
        self.comm_enabled = False

    def _comm_ready(self) -> bool:
        return self.comm_enabled and self.timer_steps % self.comm_update_period == 0

    def _is_position_valid(self, pos: PtType) -> bool:
        """ Set the current position to the position to check, check for collision, set position back """
        if pos[0] < 0 or pos[0] > self.max_x or pos[1] < 0 or pos[1] > self.max_y:
            # Out of bounds
            return False
        cur_pos = self.position
        self.center_x = pos[0]
        self.center_y = pos[1]
        walls_hit = arcade.check_for_collision_with_list(self, self.wall_list)
        self.position = cur_pos
        return len(walls_hit) == 0

    def _is_position_valid_in_occupancy_grid(self, pos: PtType) -> bool:
        cell_status = self.map.get_cell(pos[0], pos[1]).status()
        return cell_status == GridCellStatus.UNEXPLORED or cell_status == GridCellStatus.CLEAR

    def _is_position_unknown_in_occupancy_grid(self, pos: PtType) -> bool:
        cell_status = self.map.get_cell(pos[0], pos[1]).status()
        return cell_status == GridCellStatus.UNEXPLORED or cell_status == GridCellStatus.CLEAR

    def _get_position(self, test_func: FunctionType) -> fTuplePt2:
        """ Randomly select a valid position that meets the test condition """
        next_x = self.center_x
        next_y = self.center_y
        placed = False
        while not placed:

            # Randomly position
            next_x = random.randrange(self.max_x)
            next_y = random.randrange(self.max_y)

            if test_func([next_x, next_y]):
                placed = True

        return (next_x, next_y)

    def _get_valid_position(self) -> fTuplePt2:
        """ Randomly select a valid position not in the walls """
        return self._get_position(self._is_position_valid)

    def _get_valid_position_from_occupancy_grid(self) -> fTuplePt2:
        """ Randomly select a valid position not in the walls """
        return self._get_position(self._is_position_valid_in_occupancy_grid)

    def _get_unknown_position_from_occupancy_grid(self) -> fTuplePt2:
        """ Randomly select a valid position not in the walls """
        return self._get_position(self._is_position_unknown_in_occupancy_grid)

    def _get_new_path(self):
        """ This bot doesn't move """
        pass

    ## Communication ##

    async def update_comm_partners(self, wifi: WiFi.WiFi):
        """ Validate requirements are met then send occupancy map data to other bots """
        if not self._comm_ready():
            return
        await wifi.send_message(OccupancyGridMessage(self, self.name, self.map, self.timer_steps))
        for partner_map in self.partner_maps.items():
            msg = OccupancyGridMessage(self)
            msg.data = partner_map
            await wifi.send_message(msg)

    def _add_partner_map(self, bot_name: str, partner_map: OccupancyGrid, timestamp: int):
        """ Accept map data for any other bot so long as it's newer than what is currently held """
        if bot_name not in self.partner_maps or timestamp > self.partner_maps[bot_name]['timestamp']:
            self.partner_maps[bot_name] = {'timestamp': timestamp, 'map': partner_map.copy()}

    async def rcv_msg(self, msg: WiFi.Message):
        if msg.valid_receiver(self.name):
            if isinstance(msg, OccupancyGridMessage):
                self._add_partner_map(msg.bot_name, msg.bot_map, msg.timestamp)
            else:
                raise TypeError(f"Recieved an unsupported message: {type(msg)}")


    ## Updates ##

    def _update_dest(self):
        self.dest_x = self.center_x
        self.dest_y = self.center_y

    def _check_and_fix_jammed_robot(self):
        self.jam_check['position_buffer'][self.jam_check['index']] = self.position

        jammed = True
        for i in range(len(self.jam_check['position_buffer'])):
            jammed &= manhattan_dist(self.jam_check['position_buffer'][i], self.position) < self.speed

        if jammed:
            logger = RobotLogger(self.logger_id)
            logger.debug(f"Bot {self.name} is JAMMED at {self.position}")
            candidate_fixes = [[self.center_x+self.grid_size, self.center_y],
                               [self.center_x-self.grid_size, self.center_y],
                               [self.center_x, self.center_y+self.grid_size],
                               [self.center_x, self.center_y-self.grid_size]]
            for fix in candidate_fixes:
                if self._is_position_valid(fix):
                    self.center_x = fix[0]
                    self.center_y = fix[1]
                    self._update_dest()
                    self.jam_check['position_buffer'][self.jam_check['index']] = self.position
                    logger.debug(f"Bot {self.name} moved out of jam to {self.position}")

        self.jam_check['index'] = (self.jam_check['index'] + 1) % len(self.jam_check['position_buffer'])

    async def _update(self, wifi: WiFi.WiFi):
        """ Base robot doesn't move automatically """

        # Update internal clock
        self.timer_steps += 1

        await self.update_comm_partners(wifi)

    def update_speed(self):
        # X and Y diff between the two
        self.change_x = self.dest_x - self.center_x
        self.change_y = self.dest_y - self.center_y

        if abs(self.change_x) > self.speed:
            self.change_x = math.copysign(self.speed, self.change_x)
        if abs(self.change_y) > self.speed:
            self.change_y = math.copysign(self.speed, self.change_y)

    async def update(self, wifi: WiFi.WiFi, physics_engine: Optional[arcade.PhysicsEngineSimple]=None):
        await self._update(wifi)
        self.update_speed()
        hit_obstacle = []
        if physics_engine:
            hit_obstacle = physics_engine.update()
            # BUG: When the position isn't updated there is no hit obstacle returned!
        if hit_obstacle:
            RobotLogger(self.logger_id).debug(f"Bot {self.name} ran into an obstacle at {self.position}")
            if self.replan_on_collision:
                self.path = []
                self._get_new_path()
                self.dest_x, self.dest_y = self.path.pop(0)
            self._check_and_fix_jammed_robot()

    async def sensor_update(self, obstructions: list[arcade.SpriteList]):
        """ Simulate each range finder based on the simulated world """
        measure_tasks = []
        for range_finder in self.range_finders:
            measure_tasks.append(
                asyncio.create_task(
                    range_finder.measure(obstructions)))
        for task in measure_tasks:
            self.map.update(await task)


    ## Drawing ##

    def draw_sensors(self):
        """ Red dotted lines as long as the sensor range """
        for range_finder in self.range_finders:
            endpoint = range_finder.laser.endpoint(self.position)
            pts = []
            dot_count = int(range_finder.laser.max_range / self.grid_size)
            for i in range(1, dot_count):
                t = float(i)/dot_count
                x = self.position[0]*t + endpoint[0]*(1-t)
                y = self.position[1]*t + endpoint[1]*(1-t)
                pts.append([x, y])
            arcade.draw_points(pts, arcade.color.RED, 1)

    def draw_comms(self):
        """ Draw 3 rings at the communication range if communication is happening this simulation step """
        if not self._comm_ready():
            return

        radius = self.comm_range
        if radius > self.max_x:
            radius = self.grid_size
        shrink = 3
        if radius > 2*self.grid_size:
            shrink = 5
        arcade.draw_circle_outline(self.center_x, self.center_y, radius, arcade.color.BLUE)
        arcade.draw_circle_outline(self.center_x, self.center_y, radius-shrink, arcade.color.BLUE)
        arcade.draw_circle_outline(self.center_x, self.center_y, radius-2*shrink, arcade.color.BLUE)

    def draw_name(self):
        self.nametext.position = (self.center_x - self.grid_size, self.center_y + self.grid_size / 2)
        self.nametext.draw()


    ## End Simulation ##

    def save_map(self, name: Optional[str]=None):
        """ Convert the occupancy map to an image """
        if not name:
            name = self.name + " - " + str(datetime.now())
        self.map.save_map(name)
        merged_map = self.map.copy()
        for bot_name, partner_map in self.partner_maps.items():
            merged_map.add_map(partner_map['map'])
        merged_map.save_map(name + " - Merged")