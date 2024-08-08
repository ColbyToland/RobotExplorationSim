"""
A simple occupancy grid. The statistics are simplified to obstacles observed / observations of that location.

This effectively rejects spurious observations of transient obstructions while building a model of the world map.
"""

import arcade
import asyncio
from datetime import datetime
import math
from matplotlib import pyplot as plt
import numpy as np

from ExplorerConfig import ExplorerConfig
from LaserRangeFinder import Measurement
from MapTypes import WallSprite
from OccupancyGridTypes import DEFAULT_OBSTACLE_THRESHOLD, GridCell, GridCellStatus, GridResolution 
from utils import get_line


class OccupancyGrid:
    """ Store a model of the world in a grid of observation ratios """
    def __init__(self):
        """ Setup a grid space that summarizes a higher resolution rectangle

        max_x -- pixel width
        max_y -- pixel height
        grid_size -- pixel width of square obstructions in the simulated world
        resolution -- setting to adjust occupancy grid vs world map size
                        - GridResolution.LOW 1:4
                        - GridResolution.PARITY 1:1
                        - GridResolution.HIGH 4:1
        """
        self.max_x = ExplorerConfig().max_x()
        self.max_y = ExplorerConfig().max_y()
        self.grid_size = ExplorerConfig().grid_size()
        self.resolution_scale = self.grid_size # PARITY
        if ExplorerConfig().robot_map_resolution() == GridResolution.LOW:
            self.resolution_scale *= 2
        elif ExplorerConfig().robot_map_resolution() == GridResolution.HIGH:
            self.resolution_scale *= 0.5

        # Build map
        self.columns, self.rows = self._ind(self.max_x, self.max_y)
        self.map = [[GridCell() for _r in range(self.rows)] for _c in range(self.columns)]
        self._known_walls = {'list': arcade.SpriteList(use_spatial_hash=True), 
                             'map': [[None for _r in range(self.rows)] for _c in range(self.columns)]}


    # Convert between x,y and hash indices

    def _ind(self, x, y):
        """ Grid index for a given position """
        c = int(math.ceil(max(0, x-self.resolution_scale+1) / self.resolution_scale))
        r = int(math.ceil(max(0, y-self.resolution_scale+1) / self.resolution_scale))
        return c, r

    def _position(self, c, r):
        """ Center of the indexed grid square """
        x = c*self.resolution_scale+self.resolution_scale/2
        y = r*self.resolution_scale+self.resolution_scale/2
        return x, y

    def map_ind(self, x, y):
        """ Bounded grid index for a given position """
        c, r = self._ind(x, y)
        if c < 0:
            c = 0
        if c >= self.columns:
            c = self.columns-1
        if r < 0:
            r = 0
        if r >= self.rows:
            r = self.rows-1
        return c, r


    # Modify data

    def update(self, measurement, valid_distance=1):
        """ Update all grid positions covered by a single range finder laser measurement """
        endpoint = measurement.estimation(valid_distance)
        if not endpoint:
            # Update observations along the full length of the laser
            endpoint = measurement.ray()
        start_inds = self.map_ind(measurement.position[0], measurement.position[1])
        end_inds = self.map_ind(endpoint[0], endpoint[1])
        line_inds = get_line(start_inds, end_inds)
        for inds in line_inds:
            # Increment all grid cell observations and potentially one obstacle observation
            if inds == end_inds and measurement.dist != measurement.NONE:
                self.map[inds[0]][inds[1]].observe_obstacle()
            else:
                self.map[inds[0]][inds[1]].observe()

    def add_map(self, other_map):
        """ Merge other occupancy grids into this one """
        if self.columns != other_map.columns or self.rows != other_map.rows:
            raise ValueError(f"Dimension mismatch: [{self.columns}, {self.rows}] != [{map.columns}, {map.rows}]")
        for c in range(self.columns):
            for r in range(self.rows):
                self.map[c][r] += other_map.map[c][r]


    # Access data

    def get_cell(self, x, y):
        c, r = self.map_ind(x, y)
        return self.map[c][r].copy()

    def _update_known_walls_map(self, obstacle_threshold=DEFAULT_OBSTACLE_THRESHOLD):
        map_changed = False
        for c in range(self.columns):
            for r in range(self.rows):
                cell_status = self.map[c][r].status(obstacle_threshold)
                if cell_status == GridCellStatus.OBSTACLE:
                    if not isinstance(self._known_walls['map'][c][r], WallSprite):
                        wall = WallSprite()
                        wall.center_x, wall.center_y = self._position(c, r)
                        self._known_walls['map'][c][r] = wall
                        map_changed = True
                elif isinstance(self._known_walls['map'][c][r], WallSprite):
                    self._known_walls['map'][c][r] = None
                    map_changed = True
        return map_changed

    def _update_known_walls_list(self):
        self._known_walls['list'] = arcade.SpriteList(use_spatial_hash=True)
        for c in range(self.columns):
            for r in range(self.rows):
                if isinstance(self._known_walls['map'][c][r], WallSprite):
                    self._known_walls['list'].append(self._known_walls['map'][c][r])

    def get_known_walls(self, obstacle_threshold=DEFAULT_OBSTACLE_THRESHOLD, update=True):
        """ Return a list of wall sprites at the position of obstructions """

        # The known walls are only updated when this is called and the wall list is
        # maintained between calls to minimize sprite construction
        if update and self._update_known_walls_map(DEFAULT_OBSTACLE_THRESHOLD):
            self._update_known_walls_list()

        return self._known_walls['list']

    def save_map(self, name=None, obstacle_threshold=DEFAULT_OBSTACLE_THRESHOLD):
        """ Convert the occupancy grid to an image

        name -- desired filename
        obstacle_threshold -- minimum % of obstacle observations to identify an obstacle
        """
        obstacles = []
        unknown = []
        error = []
        for r in range(self.rows):
            for c in range(self.columns):
                x, y = self._position(c, r)
                if self.map[c][r].status(obstacle_threshold) == GridCellStatus.UNEXPLORED:
                    unknown.append([x,y])
                elif self.map[c][r].status(obstacle_threshold) == GridCellStatus.CLEAR:
                    continue
                elif self.map[c][r].status(obstacle_threshold) == GridCellStatus.OBSTACLE:
                    obstacles.append([x,y])
                else:
                    error.append([x,y])

        if not name:
            name = str(datetime.now())

        fig = plt.figure()
        if obstacles:
            obstacles = np.array(obstacles).T
            plt.plot(obstacles[:][0], obstacles[:][1], 'ks')
        if unknown:
            unknown = np.array(unknown).T
            plt.plot(unknown[:][0], unknown[:][1], 'b*')
        if error:
            error = np.array(error).T
            plt.plot(error[:][0], error[:][1], 'rX')
        plt.axis((0, self.max_x, 0, self.max_y))
        plt.savefig(name)
        plt.close(fig)

    def copy(self):
        """ Create an identical occupancy grid """
        mirror = OccupancyGrid()
        for c in range(self.columns):
            for r in range(self.rows):
                mirror.map[c][r] = self.map[c][r].copy()
        return mirror