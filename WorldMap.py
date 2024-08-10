"""
This is the base class that generates and draws the world map.
"""

import arcade

from ExplorerConfig import ExplorerConfig
from MapTypes import WallSprite


TYPE_NAME = "base"

class WorldMap:
    """ Base class for all maps

    This one builds a wide open, uninteresting map with a boundary wall.
    """

    def __init__(self):
        """ If overridden, call this at the end not the beginning so _create_grid has all needed info """
        map_generator_settings = ExplorerConfig().map_generator_settings()
        self.columns = map_generator_settings['grid_width']
        self.rows = map_generator_settings['grid_height']
        self.grid_size = ExplorerConfig().grid_size()
        self._create_map()

    def _create_grid(self) -> list[list[int]]:
        """ Create a two-dimensional grid with 1 for obstruction and 0 for open """
        return [[0 for _x in range(self.columns)] for _y in range(self.rows)]

    def _initialize_grid(self):
        """ Create a boundary wall """
        for c in range(self.columns):
            self.grid[c][0] = 1
            self.grid[c][self.rows-1] = 1
        for r in range(self.rows):
            self.grid[0][r] = 1
            self.grid[self.columns-1][r] = 1

    def _generate_sprites(self):
        """ Convert the grid to a sprite list of WallSprite """
        self.sprite_list = arcade.SpriteList(use_spatial_hash=True)
        for c in range(self.columns):
            for r in range(self.rows):
                if self.grid[c][r] == 1:
                    x = c * self.grid_size + self.grid_size / 2
                    y = r * self.grid_size + self.grid_size / 2
                    self.sprite_list.append(WallSprite(x, y))

    def _create_map(self):
        """ Orchestrate the creation functions

        Done this way so the subfunctions can be overridden. Primarily _initialize_grid
        """
        self.grid = self._create_grid()
        self._initialize_grid()
        self._generate_sprites()

    def draw(self):
        """ Draw the sprite list """
        self.sprite_list.draw()