"""
This is the initial map maker copied from an arcade demo (original comment below) with tweaked parameters.

---

This example procedurally develops a random cave based on cellular automata.

For more information, see:
https://gamedevelopment.tutsplus.com/tutorials/generate-random-cave-levels-using-cellular-automata--gamedev-9664

If Python and Arcade are installed, this example can be run from the command line with:
python -m arcade.examples.procedural_caves_cellular
"""

import random
import arcade

# How big the grid is
GRID_WIDTH = 40
GRID_HEIGHT = 40
GRID_SEED = None

# Parameters for cellular automata
CHANCE_TO_START_ALIVE = 0.4
DEATH_LIMIT = 4
BIRTH_LIMIT = 4
NUMBER_OF_STEPS = 4


def create_grid(width, height):
    """ Create a two-dimensional grid of specified size. """
    return [[0 for _x in range(width)] for _y in range(height)]


def initialize_grid(grid, seed = None):
    """ Randomly set grid locations to on/off based on chance. """
    height = len(grid)
    width = len(grid[0])
    if seed:
        random.seed(seed)
    for row in range(height):
        for column in range(width):
            if random.random() <= CHANCE_TO_START_ALIVE:
                grid[row][column] = 1


def count_alive_neighbors(grid, x, y):
    """ Count neighbors that are alive. """
    height = len(grid)
    width = len(grid[0])
    alive_count = 0
    for i in range(-1, 2):
        for j in range(-1, 2):
            neighbor_x = x + i
            neighbor_y = y + j
            if i == 0 and j == 0:
                continue
            elif neighbor_x < 0 or neighbor_y < 0 or neighbor_y >= height or neighbor_x >= width:
                # Edges are considered alive. Makes map more likely to appear naturally closed.
                alive_count += 1
            elif grid[neighbor_y][neighbor_x] == 1:
                alive_count += 1
    return alive_count


def do_simulation_step(old_grid):
    """ Run a step of the cellular automaton. """
    height = len(old_grid)
    width = len(old_grid[0])
    new_grid = create_grid(width, height)
    for x in range(width):
        for y in range(height):
            alive_neighbors = count_alive_neighbors(old_grid, x, y)
            if old_grid[y][x] == 1:
                if alive_neighbors < DEATH_LIMIT:
                    new_grid[y][x] = 0
                else:
                    new_grid[y][x] = 1
            else:
                if alive_neighbors > BIRTH_LIMIT:
                    new_grid[y][x] = 1
                else:
                    new_grid[y][x] = 0
    return new_grid

def generate_map(sprite_size, sprite_scale):
    # Create cave system using a 2D grid
    grid = create_grid(GRID_WIDTH, GRID_HEIGHT)
    initialize_grid(grid)
    for step in range(NUMBER_OF_STEPS):
        grid = do_simulation_step(grid)

    # Create sprites based on 2D grid
    # Each grid location is a sprite.
    wall_list = arcade.SpriteList(use_spatial_hash=True)
    for row in range(GRID_HEIGHT):
        for column in range(GRID_WIDTH):
            if grid[row][column] == 1:
                wall = arcade.Sprite(":resources:images/tiles/grassCenter.png", sprite_scale)
                wall.center_x = column * sprite_size + sprite_size / 2
                wall.center_y = row * sprite_size + sprite_size / 2
                wall_list.append(wall)

    return (grid, wall_list)