"""
Generate a map from an image
"""

import arcade
import cv2
import math
from matplotlib import colors
import numpy as np

from ExplorerConfig import ExplorerConfig
from WorldMap import WorldMap


TYPE_NAME = "image"

class ImageMap(WorldMap):
    """ Map generated from an image """

    POSITION_COLOR_STRS = ['px_bl', 'px_br', 'px_tl', 'px_tr', 'px_center']

    def __init__(self):
        """ Read in image and convert the open cell color before generating the map """
        settings = ExplorerConfig().map_generator_settings()
        assert TYPE_NAME in settings
        settings = settings[TYPE_NAME]

        self.scale = settings['scale']
        self.ratio = settings['ratio']
        self.draw_style = settings['draw_style']
        self.grid_size = ExplorerConfig().grid_size()

        self.img = cv2.cvtColor(cv2.imread(settings['image_file']), cv2.COLOR_BGR2RGB)

        # Grab the color for open cells before scaling
        self._set_open_cell_color(settings['open_cell_color'], settings['custom_color'])

        self.img = cv2.resize(self.img, (0,0), fx=self.scale, fy=self.scale)

        # Map size in settings is ignored and is instead basd on image size
        self.columns = int(math.ceil((self.img.shape[1]-1) / self.grid_size))
        self.rows = int(math.ceil((self.img.shape[0]-1) / self.grid_size))
        ExplorerConfig().set_map_grid_width(self.columns)
        ExplorerConfig().set_map_grid_height(self.rows)

        self.bg_sprite = arcade.Sprite(settings['image_file'], self.scale)
        self.bg_sprite.center_x = (self.img.shape[1]-1)/2
        self.bg_sprite.center_y = (self.img.shape[0]-1)/2

        self._create_map()

    def _get_position_color(self, color_str: str) -> np.array:
        """ Convert a position to the color at that position in the image """
        if color_str == 'px_bl':
            self.open_cell_color = self.img[-1,0]
        elif color_str == 'px_br':
            self.open_cell_color = self.img[-1,-1]
        elif color_str == 'px_tl':
            self.open_cell_color = self.img[0,0]
        elif color_str == 'px_tr':
            self.open_cell_color = self.img[0,-1]
        elif color_str == 'px_center':
            x = int(self.img.shape[1]/2)
            y = int(self.img.shape[0]/2)
            self.open_cell_color = self.img[y, x]
        else:
            self.open_cell_color = np.array([255,255,255]) # Default to white

    def _set_open_cell_color(self, color_str: str, custom_color: dict):
        """ Convert a color designation string to a color array """
        if color_str == 'custom':
            self.open_cell_color = np.array([custom_color['r'], custom_color['g'], custom_color['b']])
        elif color_str in self.POSITION_COLOR_STRS:
            self._get_position_color(color_str)
        elif colors.is_color_like(color_str): # convertable color string
            c = colors.to_rgb(color_str)
            self.open_cell_color = np.array([int(c[0]*255), int(c[1]*255), int(c[2]*255)])
        else:
            self.open_cell_color = np.array([255,255,255]) # Default to white

    def _open_cell_color_ratio(self, subimg: np.array) -> float:
        """ Ratio of pixels that are the open cell color """
        px_count = 0
        open_px_count = 0
        test_mat = subimg[:,:,0] == self.open_cell_color[0]
        test_mat = test_mat == (subimg[:,:,1] == self.open_cell_color[1])
        test_mat = test_mat == (subimg[:,:,2] == self.open_cell_color[2])
        open_px_count = test_mat.sum()
        px_count = test_mat.shape[0]*test_mat.shape[1]
        return open_px_count / px_count

    def _initialize_grid(self):
        """ Create obstructions from the image file """
        for c in range(self.columns):
            for r in range(self.rows):
                start_x = int(c*self.grid_size)
                start_y = int((self.rows-1-r)*self.grid_size)
                end_x = int(start_x + min(self.grid_size, self.img.shape[1]-start_x-1))
                end_y = int(start_y + min(self.grid_size, self.img.shape[0]-start_y-1))
                grid_img = self.img[start_y:end_y, start_x:end_x]
                if self._open_cell_color_ratio(grid_img) < (1-self.ratio):
                    self.grid[c][r] = 1

    def draw(self):
        """ Draw the image, the generated obstacles, or the overlay of obstacles on the image """
        if self.draw_style == 'image' or self.draw_style == 'overlay':
            self.bg_sprite.draw()
            # BUG: Image doesn't align with obstacles. This seems like a rendering problem of the background sprite
            #       or possibly a problem aligning the downsampled grid to the bg image sprite
        if self.draw_style == 'overlay':
            self.sprite_list.draw_hit_boxes(color=arcade.color.RED)
        elif self.draw_style != 'image':
            self.sprite_list.draw()