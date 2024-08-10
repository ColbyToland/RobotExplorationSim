"""
Generate a blank map with obstacles defined by a user point list
"""

from ExplorerConfig import ExplorerConfig
from WorldMap import WorldMap


TYPE_NAME = "manual"

class ManualMap(WorldMap):
    """ Map purely generated from user defined obstacles """

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