"""
This robot randomly selects a destination, navigates to it with A*, then selects another random destination.
"""

import arcade
import math

import Robot
from utils import LineSegmentCollisionDetector
import WiFi


TYPE_NAME = "naive_random"


class NaiveRandomRobot(Robot.Robot):
    """ Path planning done by random destination selection and A* """

    def __init__(self, wall_list: list[arcade.SpriteList], speed: float=5):
        super().__init__(wall_list, speed)

        self.bad_destination_count = 0

    def distance_to_goal(self) -> float:
        """ Using Manhattan distance while not using diagonal movement """
        return Robot.manhattan_dist([self.center_x, self.center_y], [self.dest_x, self.dest_y])

    def _get_new_path(self, update_obstructions: bool=True):
        """ Find a currently unknown location that is reachable based on the occupancy grid """
        known_walls = self.map.get_known_walls(update=update_obstructions)
        known_barrier_list = arcade.AStarBarrierList(self, known_walls, self.grid_size, 0, self.max_x, 0, self.max_y)
        while self.path == [] or self.path is None:
            dest = self._get_unknown_position_from_occupancy_grid()
            if arcade.has_line_of_sight(self.position, dest, known_walls):
                self.path = arcade.astar_calculate_path(self.position, dest, known_barrier_list, diagonal_movement = False)

    def _is_next_path_segment_blocked(self, update_obstructions: bool=False) -> bool:
        """ Verify the current trajectory is clear based on the occupancy grid """
        if self.center_x == self.dest_x and self.center_y == self.dest_y:
            return False
        collision_checker = LineSegmentCollisionDetector()
        collision_checker.setup_pts(self.position, [self.dest_x, self.dest_y])
        known_walls = self.map.get_known_walls(update=update_obstructions)
        reflected, obstacle, min_d = collision_checker.detect_collisions(self.grid_size, [known_walls])
        return reflected

    def _update_dest(self):
        """ Grab a new path if needed and set the next destination waypoint """
        NO_VALID_DESTINATIONS_THRESHOLD = 3
        MAX_ATTEMPTS_PER_SIM_STEP = 3

        if self.bad_destination_count >= NO_VALID_DESTINATIONS_THRESHOLD:
            # After multiple attempts, no valid destination could be found
            # Don't keep trying to avoid bogging down the simulation
            self.dest_x, self.dest_y = self.position
            return

        attempts = 0
        update_obstructions = True
        if self.path == []:
            self._get_new_path(update_obstructions)
            update_obstructions = False
            attempts += 1
        self.dest_x, self.dest_y = self.path.pop(0)

        # Make sure we don't see an obstruction
        while self._is_next_path_segment_blocked(update_obstructions):
            update_obstructions = False
            if attempts < MAX_ATTEMPTS_PER_SIM_STEP:
                self._get_new_path(update_obstructions)
                self.dest_x, self.dest_y = self.path.pop(0)
                attempts += 1
            else:
                # We couldn't find a valid destination this round so 
                self.dest_x, self.dest_y = self.position

        if self.center_x == self.dest_x and self.center_y == self.dest_y:
            self.bad_destination_count += 1
        else:
            self.bad_destination_count = 0

    async def _update(self, wifi: WiFi.WiFi):
        """ Update the next target location if needed, the current position, and communication """

        # Update internal clock
        self.timer_steps += 1

        if self.distance_to_goal() <= self.speed or self.path == [] or self._is_next_path_segment_blocked(update_obstructions=True):
            # If we're too close to the target or the new sensor data tells us the next target is unreachable then update the target destination
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