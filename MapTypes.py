"""
Shared types for maps
"""

import arcade

from ExplorerConfig import ExplorerConfig


class WallSprite(arcade.Sprite):
    """ Sprite for wall obstructions """
    def __init__(self, x=0, y=0):
        super().__init__(":resources:images/tiles/grassCenter.png", ExplorerConfig().drawing_settings()['scale'])
        self.center_x = x
        self.center_y = y