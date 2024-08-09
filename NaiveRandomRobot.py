"""
This robot randomly selects a destination, navigates to it with A*, then selects another random destination.
"""

import arcade
import math

from ExplorerConfig import ExplorerConfig
from OccupancyGrid import OccupancyGrid
import Robot
from SimulationLoggers import RobotLogger
from utils import LineSegmentCollisionDetector
import WiFi


TYPE_NAME = "naive_random"


class NaiveRandomRobot(Robot.Robot):
    """ Path planning done by random destination selection and A* """

    def __init__(self, robot_group_id: int, wall_list: list[arcade.SpriteList], speed: float=5):
        super().__init__(robot_group_id, wall_list, speed)

        self.bad_destination_count = 0
        self.nav_map = OccupancyGrid(ExplorerConfig().robot_map_resolution(self._robot_group_id))

    def distance_to_goal(self) -> float:
        """ Using Manhattan distance while not using diagonal movement """
        return Robot.manhattan_dist([self.center_x, self.center_y], [self.dest_x, self.dest_y])

    def _get_new_path(self, update_obstructions: bool=True):
        """ Find a currently unknown location that is reachable based on the occupancy grid """
        known_walls = self.nav_map.get_known_walls(update=update_obstructions)
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
        known_walls = self.nav_map.get_known_walls(update=update_obstructions)
        reflected, obstacle, min_d = collision_checker.detect_collisions(self.grid_size, [known_walls])
        return reflected

    def _add_partner_map(self, bot_name: str, partner_map: OccupancyGrid, timestamp: int):
        """ User base robot's message handler then update nav map if appropriate """
        super()._add_partner_map(bot_name, partner_map, timestamp)
        if bot_name not in self.partner_maps or timestamp > self.partner_maps[bot_name]['timestamp']:
            self.nav_map.add_map(partner_map)
            self.nav_map_updated = True

    async def sensor_update(self, obstructions: list[arcade.SpriteList]):
        """ Do measurements in base robot's function then add this bots map to its nav map """
        await super().sensor_update(obstructions)
        self.nav_map.add_map(self.map)
        self.nav_map_updated = True

    def _update_dest(self):
        """ Grab a new path if needed and set the next destination waypoint """
        NO_VALID_DESTINATIONS_THRESHOLD = 3
        MAX_ATTEMPTS_PER_SIM_STEP = 3

        if self.bad_destination_count >= NO_VALID_DESTINATIONS_THRESHOLD:
            # After multiple attempts, no valid destination could be found
            # Don't keep trying to avoid bogging down the simulation
            self.dest_x, self.dest_y = self.position
            self.path = []
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
            if (update_obstructions and attempts == 0) or (not update_obstructions and attempts == 1):
                RobotLogger(self.logger_id).debug(f"Bot {self.name} is blocked at {self.position} trying to go to [{self.dest_x}, {self.dest_y}]")
            update_obstructions = False
            if attempts < MAX_ATTEMPTS_PER_SIM_STEP:
                self._get_new_path(update_obstructions)
                self.dest_x, self.dest_y = self.path.pop(0)
                attempts += 1
            else:
                # We couldn't find a valid destination this round so 
                RobotLogger(self.logger_id).debug(f"Bot {self.name} is blocked at {self.position} and couldn't find a valid new position")
                self.dest_x, self.dest_y = self.position
                break

        if self.center_x == self.dest_x and self.center_y == self.dest_y:
            self.bad_destination_count += 1
        else:
            self.bad_destination_count = 0

    async def _update(self, wifi: WiFi.WiFi):
        """ Update the next target location if needed, the current position, and communication """

        # Update internal clock
        self.timer_steps += 1

        if (self.distance_to_goal() <= self.speed or
            self.path == [] or
            (self.nav_map_updated and self._is_next_path_segment_blocked(update_obstructions=True))):
            # If we're too close to the target or the new sensor data tells us the next target is unreachable then update the target destination
            self._update_dest()
        self.nav_map_updated = False

        await self.update_comm_partners(wifi)