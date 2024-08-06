"""
This robot randomly selects a destination, navigates to it with A*, then selects another random destination.
"""

import arcade
import math
import numpy as np

import Robot
from LaserRangeFinder import Laser


TYPE_NAME = "naive_random"


def line_length(start_pt, end_pt):
    return float(np.linalg.norm(np.array(start_pt)-np.array(end_pt)))

def line_orientation(start_pt, end_pt):
    return float(np.arctan2(end_pt[1]-start_pt[1], end_pt[0]-start_pt[0]))

class NaiveRandomRobot(Robot.Robot):
    """ Path planning done by random destination selection and A* """

    def __init__(self, wall_list, speed = 5):
        super().__init__(wall_list, speed)

        self.bad_destination_count = 0

    def distance_to_goal(self):
        # Using Manhattan distance while not using diagonal movement
        return Robot.manhattan_dist([self.center_x, self.center_y], [self.dest_x, self.dest_y])

    def _get_new_path_from_occupancy_grid(self):
        known_walls = self.map.get_known_walls()
        known_barrier_list = arcade.AStarBarrierList(self, known_walls, self.grid_size, 0, self.max_x, 0, self.max_y)
        while self.path == [] or self.path == None:
            dest = self._get_unknown_position_from_occupancy_grid()
            if arcade.has_line_of_sight(self.position, dest, known_walls):
                self.path = arcade.astar_calculate_path(self.position, dest, known_barrier_list, diagonal_movement = False)

    def _update_dest(self):
        NO_VALID_DESTINATIONS_THRESHOLD = 3
        MAX_ATTEMPTS_PER_SIM_STEP = 3

        if self.bad_destination_count >= NO_VALID_DESTINATIONS_THRESHOLD:
            # After multiple attempts, no valid destination could be found
            # Don't keep trying to avoid bogging down the simulation
            return

        attempts = 0
        if self.path == []:
            self._get_new_path_from_occupancy_grid()
            attempts += 1
        self.dest_x, self.dest_y = self.path.pop(0)

        if attempts == 0:
            # Make sure we don't see an obstruction
            collision_checker = Laser(self.grid_size/2., 
                                      line_length(self.position, [self.dest_x, self.dest_y]), 
                                      line_orientation(self.position, [self.dest_x, self.dest_y]))
            while collision_checker.bresenham_line_hash_lookup(self.position, self.map.get_known_walls().spatial_hash):
                if attempts < MAX_ATTEMPTS_PER_SIM_STEP:
                    self._get_new_path_from_occupancy_grid()
                    attempts += 1
                else:
                    # We couldn't find a valid destination this round so 
                    self.dest_x, self.dest_y = self.position

        if self.center_x == self.dest_x and self.center_y == self.dest_y:
            self.bad_destination_count += 1
        else:
            self.bad_destination_count = 0

    async def _update(self, wifi):
        """ Update the next target location if needed, the current position, and communication """

        # Update internal clock
        self.timer_steps += 1

        if self.distance_to_goal() <= self.speed or self.path == []:
            self._update_dest()

        # X and Y diff between the two
        x_diff = self.dest_x - self.center_x
        y_diff = self.dest_y - self.center_y

        if abs(x_diff) > self.speed:
            x_diff = math.copysign(self.speed, x_diff)
        if abs(y_diff) > self.speed:
            y_diff = math.copysign(self.speed, y_diff)

        self.center_x += x_diff
        self.center_y += y_diff

        await self.update_comm_partners(wifi)