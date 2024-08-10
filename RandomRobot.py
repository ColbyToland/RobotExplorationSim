"""
This robot randomly selects a destination, navigates to it with A*, then selects another random destination.
"""

import arcade

import Robot
import WiFi


TYPE_NAME = "random"


class RandomRobot(Robot.Robot):
    """ Path planning done by random destination selection and A* """

    def distance_to_goal(self) -> float:
        """ Using Manhattan distance while not using diagonal movement """
        return Robot.manhattan_dist([self.center_x, self.center_y], [self.dest_x, self.dest_y])

    def _get_new_path(self):
        """ Find a path to a random reachable location """
        while self.path == [] or self.path is None:
            dest = self._get_valid_position()
            if arcade.has_line_of_sight(self.position, dest, self.wall_list):
                self.path = arcade.astar_calculate_path(self.position, dest, self.barrier_list, diagonal_movement = False)

    def _update_dest(self):
        """ Get a new path if needed and set the next destination along that path """
        if self.path == []:
            self._get_new_path()
        self.dest_x, self.dest_y = self.path.pop(0)

    async def _update(self, wifi: WiFi.WiFi):
        """ Update the next target location if needed, the current position, and communication """

        self.timer_steps += 1

        if self.distance_to_goal() <= self.speed or self.path == []:
            self._update_dest()

        await self.update_comm_partners(wifi)