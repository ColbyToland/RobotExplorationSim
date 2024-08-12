"""
This robot randomly selects a destination, navigates to it with A*, then selects another random destination.
"""

import arcade
from enum import Enum
import math

import NaiveRandomRobot
import numpy as np
from OccupancyGridTypes import GridCellStatus
from SimulationLoggers import RobotLogger
from typing import Optional, Self
from utils import fTuplePt2, iTuplePt2


TYPE_NAME = "linear_sweeper"


class LinearSweepStyle(Enum):
    """ Summary description of path planning direction """
    NONE = 0
    UP = 1
    DOWN = 2
    LEFT = 3
    RIGHT = 4
    @classmethod
    def flip(cls, value: Self) -> Self:
        if value == cls.UP:
            return cls.DOWN
        elif value == cls.DOWN:
            return cls.UP
        elif value == cls.LEFT:
            return cls.RIGHT
        elif value == cls.RIGHT:
            return cls.LEFT
        return cls.NONE


class Directions(Enum):
    NONE = (0,0)
    UP = (0,1)
    DOWN = (0,-1)
    LEFT = (-1,0)
    RIGHT = (1,0)
    @classmethod
    def flip(cls, o: Self) -> Self:
        return cls((-1*o.value[0], -1*o.value[1]))
    @classmethod
    def perp(cls, o: Self) -> tuple[Self, Self]:
        perp1 = cls((o.value[1], o.value[0]))
        perp2 = cls((-1*o.value[1], -1*o.value[0]))
        return (perp1, perp2)


class LinearSweepRobot(NaiveRandomRobot.NaiveRandomRobot):
    """ Path planning done by selecting a linear sweep destination """

    def __init__(self, robot_group_id: int, wall_list: list[arcade.SpriteList], speed: float=5):
        super().__init__(robot_group_id, wall_list, speed)

        self.sweep_direction = LinearSweepStyle.UP
        self.done = False

    def _get_bot_direction_vec(self) -> iTuplePt2:
        return (round(math.cos(self.angle)), round(math.sin(self.angle)))

    def _find_unknown_in_direction(self, direction: Directions, sweep_step: fTuplePt2=(0,0)) -> Optional[fTuplePt2]:
        """ Look along the direction specified for an unknown position

        direction -- unit length tuple describing the direction of search
        sweep_step -- optional distance vec to increment along and repeat searchs
        """
        steps = 3
        if sweep_step == (0,0):
            steps = 1
        for i in range(steps):
            start_pt = (self.center_x+i*sweep_step[0], self.center_y+i*sweep_step[0])
            start_inds = self.nav_map.map_ind(start_pt[0], start_pt[1])
            end_inds = start_inds
            ind_step = (1,1)

            # Change the end indices and step direction to the correct direction
            if direction == Directions.UP:
                end_inds = (start_inds[0], self.nav_map.rows)
            if direction == Directions.DOWN:
                end_inds = (start_inds[0], 0)
                ind_step = (1,-1)
            elif direction == Directions.LEFT:
                end_inds = (0, start_inds[1])
                ind_step = (-1,1)
            elif direction == Directions.RIGHT:
                end_inds = (self.nav_map.columns, start_inds[0])

            # Adjust the end indices to account for range going to 1 step less than the end value
            end_inds = (end_inds[0]+ind_step[0], end_inds[1]+ind_step[1])

            unknown_found = False
            dest_inds = start_inds
            for c in range(start_inds[0], end_inds[0], ind_step[0]):
                for r in range(start_inds[1], end_inds[1], ind_step[1]):
                    if self.nav_map.get_cell(c,r).status() == GridCellStatus.UNEXPLORED:
                        unknown_found = True
                    elif self.nav_map.get_cell(c,r).status() == GridCellStatus.OBSTACLE:
                        break
                    # save the furthest position that is not an obstacle
                    dest_inds = (c, r)
            if unknown_found:
                return self.nav_map.ind_to_position(dest_inds[0], dest_inds[1])
        return None

    def _check_dest(self, dest: fTuplePt2, known_walls: arcade.SpriteList) -> bool:
        """ Make sure we have line of sight to this destination """
        return dest is not None and arcade.has_line_of_sight(self.position, dest, known_walls)

    def _get_sweep_dest(self, known_walls: arcade.SpriteList) -> Optional[fTuplePt2]:
        """ Find the next unknown destination in the sweep direction """

        sweep_dir = Directions[self.sweep_direction.name]
        bot_dir = Directions(self._get_bot_direction_vec())

        if bot_dir == sweep_dir:
            # If moving in the sweep direction, check the two perpendicular directions for a candidate location
            perp_dirs = Directions.perp(bot_dir)
            for dir_vec in perp_dirs:
                dest = self._find_unknown_in_direction(dir_vec)
                if self._check_dest(dest, known_walls):
                    return dest
        else:
            opposite_dir = Directions.flip(bot_dir)
            for _ in range(2):
                # Look in the opposite direction
                dest = self._find_unknown_in_direction(opposite_dir)
                if self._check_dest(dest, known_walls):
                    return dest

                # Look for the next position one bot size (grid size) in the sweep direction and in the current bot direction/angle
                sweep_step = (self.grid_size*sweep_dir.value[0], self.grid_size*sweep_dir.value[1])
                dest = self._find_unknown_in_direction(bot_dir, sweep_step)
                if self._check_dest(dest, known_walls):
                    return dest

                # Look for the next position one bot size (grid size) in the sweep direction and in the opposite of the current bot direction/angle
                dest = self._find_unknown_in_direction(opposite_dir, sweep_step)
                if self._check_dest(dest, known_walls):
                    return dest

                # Change sweep direction and repeat
                self.sweep_direction = LinearSweepStyle.flip(self.sweep_direction)
                RobotLogger(self.logger_id).debug(
                    f"Bot {self.name} is switching sweep direction at {self.position} from {LinearSweepStyle.flip(self.sweep_direction).name} to {self.sweep_direction.name}")
                sweep_dir = Directions[self.sweep_direction.name]

        # If no candidates, set dest = position and done = True
        self.dest_x = self.center_x
        self.dest_y = self.center_y
        self.done = True
        return None

    def _get_new_path(self, update_obstructions: bool=True):
        """ Find a currently unknown location that is reachable based on the occupancy grid """
        known_walls = self.nav_map.get_known_walls(update=update_obstructions)
        known_barrier_list = arcade.AStarBarrierList(self, known_walls, self.grid_size, 0, self.max_x, 0, self.max_y)
        dest = self._get_sweep_dest(known_walls)
        if dest is not None:
            self.path = arcade.astar_calculate_path(self.position, dest, known_barrier_list, diagonal_movement = False)
        else:
            self.path = []

    def _update_dest(self):
        """ Perform the parent function and update the movement direction """
        super()._update_dest()

        # Update the movement direction for use by the sweep destination selection
        self.angle = np.arctan2(self.dest_y - self.center_y, self.dest_x - self.center_x)

    def _update_dest(self):
        """ Grab a new path if needed and set the next destination waypoint """

        if self.done:
            return

        if self.path == [] or self._is_next_path_segment_blocked(update_obstructions=True):
            self._get_new_path(update_obstructions=False)
        self.dest_x, self.dest_y = self.path.pop(0)
        self.angle = float(np.arctan2(self.dest_y - self.center_y, self.dest_x - self.center_x))