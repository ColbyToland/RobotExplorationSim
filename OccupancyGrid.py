from datetime import datetime
from enum import Enum
import math
from matplotlib import pyplot as plt
import numpy as np

from bresenham_line import get_line
from LaserRangeFinder import Measurement

class GridResolution(Enum):
    LOW = 0
    PARITY = 1
    HIGH = 2

class GridCellStatus(Enum):
    UNEXPLORED = -1
    CLEAR = 0
    OBSTACLE = 1

class GridCell:
    def __init__(self):
        # default to UNEXPLORED_CELL
        self._obstacles = -1
        self._observations = -1

    def _observe(self):
        if self.status() == GridCellStatus.UNEXPLORED:
            self._obstacles = 0
            self._observations = 0

    def observe(self):
        self._observe()
        self._observations += 1

    def observe_obstacle(self):
        self.observe()
        self._obstacles += 1

    def status(self, obstacle_threshold=0.5):
        if self._observations == -1:
            return GridCellStatus.UNEXPLORED
        pct = self._obstacles / self._observations
        if pct > obstacle_threshold:
            return GridCellStatus.OBSTACLE 
        return GridCellStatus.CLEAR

    def __iadd__(self, cell):
        if cell.status() != GridCellStatus.UNEXPLORED:
            self._observe()
            self._observations += cell._observations
            self._obstacles += cell._obstacles
        return self

    def copy(self):
        mirror = GridCell()
        mirror._obstacles = self._obstacles
        mirror._observations = self._observations
        return mirror

    def __eq__(self, other):
        return self._obstacles == other._obstacles and self._observations == other._observations

    def __ne__(self, other):
        return not self.__eq__(other)

class OccupancyGrid:
    def __init__(self, max_x, max_y, grid_size, resolution):
        self.max_x = max_x
        self.max_y = max_y
        self.grid_size = grid_size
        self.resolution = resolution
        self.resolution_scale = self.grid_size # PARITY
        if self.resolution == GridResolution.LOW:
            self.resolution_scale *= 2
        elif self.resolution == GridResolution.HIGH:
            self.resolution_scale *= 0.5

        self.columns, self.rows = self._ind(max_x, max_y)
        self.map = [[GridCell() for _r in range(self.rows)] for _c in range(self.columns)]

    def _ind(self, x, y):
        c = int(math.ceil(max(0, x-self.resolution_scale+1) / self.resolution_scale))
        r = int(math.ceil(max(0, y-self.resolution_scale+1) / self.resolution_scale))
        return c, r

    def _position(self, c, r):
        # Bottom left corner of the grid square
        x = c*self.resolution_scale
        y = r*self.resolution_scale
        return x, y

    def map_ind(self, x, y):
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

    def update(self, measurement, valid_distance=1):
        endpoint = measurement.estimation(valid_distance)
        if not endpoint:
            endpoint = measurement.ray()
        start_inds = self.map_ind(measurement.position[0], measurement.position[1])
        end_inds = self.map_ind(endpoint[0], endpoint[1])
        line_inds = get_line(start_inds, end_inds)
        for inds in line_inds:
            if inds == end_inds and measurement.dist != measurement.NONE:
                self.map[inds[0]][inds[1]].observe_obstacle()
            else:
                self.map[inds[0]][inds[1]].observe()

    def save_map(self, name=None, obstacle_threshold=0.5):
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

    def copy(self):
        mirror = OccupancyGrid(self.max_x, self.max_y, self.grid_size, self.resolution)
        for c in range(self.columns):
            for r in range(self.rows):
                mirror.map[c][r] = self.map[c][r].copy()
        return mirror

    def add_map(self, other_map):
        if self.columns != other_map.columns or self.rows != other_map.rows:
            raise ValueError(f"Dimension mismatch: [{self.columns}, {self.rows}] != [{map.columns}, {map.rows}]")
        for c in range(self.columns):
            for r in range(self.rows):
                self.map[c][r] += other_map.map[c][r]