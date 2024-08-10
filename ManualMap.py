"""
Generate a blank map with obstacles defined by a user point list
"""

import math

from ExplorerConfig import ExplorerConfig
from utils import iTuplePt2, PtType
from WorldMap import WorldMap


TYPE_NAME = "manual"

class ManualMap(WorldMap):
    """ Map purely generated from user defined obstacles """

    def _ind(self, x: float, max_i: int) -> int:
        """ Bound conversion of px position component to index """
        i = math.floor(x / self.grid_size)
        i = max(0, i)
        i = min(max_i, i)
        return i

    def _rc_from_xy(self, x: float, y: float) -> iTuplePt2:
        """ Bound conversion of px to indices """
        c = self._ind(x, self.columns-1)
        r = self._ind(y, self.rows-1)
        return c, r

    def _initialize_grid(self):
        """ Create user defined obstructions """
        settings = ExplorerConfig().map_generator_settings()
        assert TYPE_NAME in settings
        pts = settings[TYPE_NAME]['points']
        px_not_indices = settings[TYPE_NAME]['px_not_indices']
        for pt in pts:
            c = pt['x']
            r = pt['y']
            if px_not_indices:
                c, r = self._rc_from_xy(c, r)
            self.grid[c][r] = 1