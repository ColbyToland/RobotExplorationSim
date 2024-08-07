"""
Shared types for maps
"""

import arcade

from ExplorerConfig import ExplorerConfig


class WallSprite(arcade.Sprite):
    """ Sprite for wall obstructions """
    def __init__(self):
        super().__init__(":resources:images/tiles/grassCenter.png", ExplorerConfig().drawing_settings()['scale'])