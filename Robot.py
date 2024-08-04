"""
Based on astar_pathfinding and follow_path demos
"""

import arcade
from datetime import datetime
import math
import random
import numpy as np

from LaserRangeFinder import LaserRangeFinder, Measurement
from OccupancyGrid import GridResolution, OccupancyGrid


SENSOR_COUNT = 8
MAP_RESOLUTION = GridResolution.PARITY

assigned_robot_names = []

class Robot(arcade.Sprite):
    def __init__(self, scale, wall_list, max_x, max_y, speed = 5):
        super().__init__(":resources:images/animated_characters/robot/robot_idle.png", scale)

        self.timer_steps= 0
        self.name = None
        self.gen_name()
        self.wall_list = wall_list
        self.max_x = max_x
        self.max_y = max_y
        self.center_x, self.center_y = self.get_next_position()
        self.dest_x, self.dest_y = self.center_x, self.center_y
        self.speed = speed
        self.grid_size = 128*scale

        # path planning
        self.barrier_list = arcade.AStarBarrierList(self, self.wall_list, self.grid_size, 0, max_x, 0, max_y)
        self.path = []

        # sensors
        self.laser_half_width = self.grid_size / 2 + 1
        self.range_finders = []
        max_range = 5*self.grid_size # Limited view
        #max_range=1.1*max([max_x, max_y]) # Unlimited view
        for i in range(SENSOR_COUNT): # replicate v3 setup
            self.range_finders.append(LaserRangeFinder(self, 
                                                       self.laser_half_width, 
                                                       max_range=max_range,
                                                       orientation=i*2*math.pi/SENSOR_COUNT))

        # map
        self.map = OccupancyGrid(self.max_x, self.max_y, self.grid_size, MAP_RESOLUTION)
        self.partner_maps = {}

        # comms
        self.comm_enabled = False
        self.comm_range = 0
        self.comm_frequency = 0
        self.comm_partners = []

    def gen_name(self):
        colors = ["Red",
                  "Green",
                  "Blue",
                  "Black",
                  "White",
                  "Gold",
                  "Silver"]
        animals = ["Wolf",
                   "Dragon",
                   "Falcon",
                   "Viper",
                   "Shark",
                   "Hornet"]

        while not self.name:
            candidate = random.choice(colors) + " " + random.choice(animals)
            if candidate not in assigned_robot_names:
                self.name = candidate
                assigned_robot_names.append(self.name)

    def enable_comms(self, wireless_range=math.inf, frequency=1):
        self.comm_enabled = True
        self.comm_range = wireless_range
        self.comm_frequency = frequency

    def add_comm_subscriber(self, bot):
        if not bot in self.comm_partners:
            self.comm_partners.append(bot)

    def _comm_ready(self):
        return self.comm_enabled and self.timer_steps % self.comm_frequency == 0

    def update_comm_partners(self):
        if not self._comm_ready():
            return
        for bot in self.comm_partners:
            if not bot.comm_enabled:
                continue
            d = float(np.linalg.norm(np.array(bot.position)-np.array(self.position)))
            if d > self.comm_range or d > bot.comm_range:
                continue
            bot.add_partner_map(self.name, self.map, self.timer_steps)
            for bot_name, partner_map in self.partner_maps.items():
                bot.add_partner_map(bot_name, partner_map['map'], partner_map['timestamp'])

    def add_partner_map(self, bot_name, partner_map, timestamp):
        if not bot_name in self.partner_maps or timestamp > self.partner_maps[bot_name]['timestamp']:
            self.partner_maps[bot_name] = {'timestamp': timestamp, 'map': partner_map.copy()}

    def get_next_position(self):
        # Randomly place the player. If we are in a wall, repeat until we aren't.
        cur_x = self.center_x
        cur_y = self.center_y
        placed = False
        while not placed:

            # Randomly position
            self.center_x = random.randrange(self.max_x)
            self.center_y = random.randrange(self.max_y)

            # Are we in a wall?
            walls_hit = arcade.check_for_collision_with_list(self, self.wall_list)
            if len(walls_hit) == 0:
                # Not in a wall! Success!
                placed = True

        # Return the safe position and reset to original position
        next_x = self.center_x
        next_y = self.center_y
        self.center_x = cur_x
        self.center_y = cur_y

        return (next_x, next_y)

    def distance_to_goal(self):
    	# Using Manhattan distance while not using diagonal movement
    	return (abs(self.center_x - self.dest_x) + abs(self.center_y - self.dest_y))

    def update(self):
        self.timer_steps += 1

        if self.distance_to_goal() <= self.speed or self.path == []:
        	if self.path == []:
	        	while self.path == [] or self.path == None:
	        		dest = self.get_next_position()
	        		if arcade.has_line_of_sight(self.position, dest, self.wall_list):
	        			self.path = arcade.astar_calculate_path(self.position, dest, self.barrier_list, diagonal_movement = False)
        	self.dest_x, self.dest_y = self.path.pop(0)

        # X and Y diff between the two
        x_diff = self.dest_x - self.center_x
        y_diff = self.dest_y - self.center_y

        if abs(x_diff) > self.speed:
        	x_diff = math.copysign(self.speed, x_diff)
        if abs(y_diff) > self.speed:
        	y_diff = math.copysign(self.speed, y_diff)

        self.center_x += x_diff
        self.center_y += y_diff

        self.update_comm_partners()

    def sensor_update(self, obstructions):
        for range_finder in self.range_finders:
            self.map.update(range_finder.measure(obstructions))

    def draw_sensors(self):
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

    def save_map(self, name=None):
        if not name:
            name = self.name + " - " + str(datetime.now())
        self.map.save_map(name)
        merged_map = self.map.copy()
        for bot_name, partner_map in self.partner_maps.items():
            merged_map.add_map(partner_map['map'])
        merged_map.save_map(name + " - Merged")