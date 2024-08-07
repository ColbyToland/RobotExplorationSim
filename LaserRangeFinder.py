"""
Look for an intersection along a line segment and return the distance from that intersection to the robot.

However, there is some error because the distance is from the robot center to the obstruction center NOT
the distance to the point of intersection.

This is a structured noise unlike an actual range finder but it serves as a stand-in for that behavior.
"""

import asyncio
import math
import numpy as np

from utils import LineSegmentCollisionDetector


class Measurement:
    """ Stores a single measurement from the range finder """

    # Even if a reading does not get a reflection, we still want to return that measurement attempt
    NONE = -1

    def __init__(self, position, orientation, dist, max_range):
        self.position = position
        self.orientation = orientation
        self.dist = dist
        self.max_range = max_range

    def _project(self, d):
        return [self.position[0] + d*math.cos(self.orientation), 
                self.position[1] + d*math.sin(self.orientation)]

    def estimation(self, min_valid_range):
        """ Use the distance to project out where the obstruction was """
        estimate = None
        if self.dist != self.NONE and self.dist >= min_valid_range:
            estimate = self._project(self.dist)
        return estimate

    def ray(self):
        """ The furthest point that this sensor could detect an obstruction """
        return self._project(self.max_range)


class Laser(LineSegmentCollisionDetector):
    def __init__(self, laser_width, max_range, orientation):
        super().__init__()
        self.setup_polar([0,0], max_range, orientation)
        self.laser_width = laser_width

    @property
    def max_range(self):
        return self.length

    @max_range.setter
    def max_range(self, value):
        self.length = value

    def get_reflection_distance(self, position, obstructions):
        reflected, obstacle, min_d = self.detect_collisions(self.laser_width, obstructions, position)
        return reflected, min_d
    

class LaserRangeFinder:
    """ Simulate a laser range finder sensor """

    def __init__(self, bot, laser_width, max_range, orientation):
        self.bot = bot
        self.laser = Laser(laser_width, max_range, orientation)

    async def measure(self, obstructions):
        """ measure the distance to the nearest obstruction along a line segment

        obstructions must be a list of sprite lists with spatial hashing
        """

        reflected, min_d = self.laser.get_reflection_distance(self.bot.position, obstructions)

        if reflected:
            # Only send a distance if it's within the laser's range
            return Measurement(self.bot.position, self.laser.orientation, min_d, self.laser.max_range)
        
        # Return a measurement even if an obstruction was observed
        return Measurement(self.bot.position, self.laser.orientation, Measurement.NONE, self.laser.max_range)
