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
from enum import Enum
import math
import random

from ExplorerConfig import ExplorerConfig
from LaserRangeFinder import LaserRangeFinder, Measurement
from OccupancyGrid import GridResolution, OccupancyGrid
import WiFi


TYPE_NAME = "base"


class OccupancyGridMessage(WiFi.Message):
    TYPE = "Occupancy Grid"
    def __init__(self, sender, bot_name=None, oc_grid=None, timestamp=None, receivers=WiFi.Message.BROADCAST):
        super().__init__(sender, msg_type = OccupancyGridMessage.TYPE, receivers=receivers)
        self.bot_name = bot_name
        self.bot_map = oc_grid
        self.timestamp = timestamp

    @property
    def data(self):
        return (self.bot_name, {'map': self.bot_map, 'timestamp': self.timestamp})
    
    @data.setter
    def data(self, value):
        self.bot_name = value[0]
        self.bot_map = value[1]['map']
        self.timestamp = value[1]['timestamp']


# Store the assigned robot names in a global to avoid duplicates
assigned_robot_names = []

def manhattan_dist(p1, p2):
    return (abs(p1[0]-p2[0])+abs(p1[1]-p2[1]))

class Robot(arcade.Sprite):
    """ Sprite to simulate a single robot """

    ## Setup ##

    def __init__(self, wall_list, max_x, max_y, speed = 5):
        """ Initialization takes care of all setup. There are no additional setup functions. """

        drawing_settings = ExplorerConfig().drawing_settings()
        super().__init__(":resources:images/animated_characters/robot/robot_idle.png", drawing_settings['scale'])

        self.timer_steps= 0
        self.name = None
        self.gen_name()
        self.wall_list = wall_list
        self.max_x = max_x
        self.max_y = max_y
        self.center_x, self.center_y = self._get_valid_position()
        self.dest_x, self.dest_y = self.center_x, self.center_y
        self.speed = speed
        self.grid_size = drawing_settings['size']*drawing_settings['scale']

        # path planning
        self.barrier_list = arcade.AStarBarrierList(self, self.wall_list, self.grid_size, 0, max_x, 0, max_y)
        self.path = []

        self.jam_check = {'position_buffer': [], 'index':0}
        for i in range(10):
            self.jam_check['position_buffer'].append([self.center_x + i*self.speed, self.center_y + i*self.speed])

        # sensors
        robot_sensor_settings = ExplorerConfig().robot_sensor_settings()
        self.laser_half_width = robot_sensor_settings['beam_grid_scale']*self.grid_size / 2 + 1
        self.range_finders = []
        max_range = robot_sensor_settings['range_grid_scale']*self.grid_size
        for i in range(robot_sensor_settings['count']):
            self.range_finders.append(LaserRangeFinder(self, 
                                                       self.laser_half_width, 
                                                       max_range=max_range,
                                                       orientation=i*2*math.pi/robot_sensor_settings['count']))

        # map
        self.map = OccupancyGrid(self.max_x, self.max_y, self.grid_size, ExplorerConfig().robot_map_resolution())
        self.partner_maps = {}

        # comms
        robot_comm_settings = ExplorerConfig().robot_comm_settings()
        self.comm_enabled = True
        self.comm_range = robot_comm_settings['wireless_range_grid_scale']*self.grid_size
        self.comm_update_period = robot_comm_settings['update_period']

    def gen_name(self):
        """ Randomly generate a unique name from name part lists """
        global assigned_robot_names
        name_parts = ExplorerConfig().robot_name_gen_parameters()
        while not self.name:
            candidate = ""
            for name_part_list in name_parts:
                if candidate != "":
                    candidate += " "
                candidate += random.choice(name_part_list)
            if candidate not in assigned_robot_names:
                self.name = candidate
                assigned_robot_names.append(self.name)

    def enable_comms(self):
        """ Turn on comms """
        self.comm_enabled = True

    def disable_comms(self):
        """ Turn off comms """
        self.comm_enabled = False

    def _comm_ready(self):
        return self.comm_enabled and self.timer_steps % self.comm_update_period == 0

    def _is_position_valid(self, pos):
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

    def _get_valid_position(self):
        """ Randomly select a valid position not in the walls """
        next_x = self.center_x
        next_y = self.center_y
        placed = False
        while not placed:

            # Randomly position
            next_x = random.randrange(self.max_x)
            next_y = random.randrange(self.max_y)

            if self._is_position_valid([next_x, next_y]):
                placed = True

        return (next_x, next_y)


    ## Communication ##

    async def update_comm_partners(self, wifi):
        """ Validate requirements are met then send occupancy map data to other bots """
        if not self._comm_ready():
            return
        await wifi.send_message(OccupancyGridMessage(self, self.name, self.map, self.timer_steps))
        for partner_map in self.partner_maps.items():
            msg = OccupancyGridMessage(self)
            msg.data = partner_map
            await wifi.send_message(msg)

    def _add_partner_map(self, bot_name, partner_map, timestamp):
        """ Accept map data for any other bot so long as it's newer than what is currently held """
        if not bot_name in self.partner_maps or timestamp > self.partner_maps[bot_name]['timestamp']:
            self.partner_maps[bot_name] = {'timestamp': timestamp, 'map': partner_map.copy()}

    async def rcv_msg(self, msg):
        if not isinstance(msg, WiFi.Message):
            raise TypeError(f"Received an invalid message: {type(msg)}")
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

        self.jam_check['index'] = (self.jam_check['index'] + 1) % len(self.jam_check['position_buffer'])

    async def _update(self, wifi):
        """ Base robot doesn't move automatically """

        # Update internal clock
        self.timer_steps += 1

        await self.update_comm_partners(wifi)

    async def update(self, wifi, physics_engine=None):
        prev_pos = self.position
        await self._update(wifi)
        new_pos = self.position
        if physics_engine:
            physics_engine.update()
        if new_pos != self.position:
            # Async physics can cause bots to get pushed around so pause in place and pick a new path
            self.position = prev_pos
            self._get_new_path()
            self.dest_x, self.dest_y = self.path.pop(0)
        self._check_and_fix_jammed_robot()

    async def sensor_update(self, obstructions):
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


    ## End Simulation ##

    def save_map(self, name=None):
        """ Convert the occupancy map to an image """
        if not name:
            name = self.name + " - " + str(datetime.now())
        self.map.save_map(name)
        merged_map = self.map.copy()
        for bot_name, partner_map in self.partner_maps.items():
            merged_map.add_map(partner_map['map'])
        merged_map.save_map(name + " - Merged")