"""
A random world map using the cellular automata algorithm in the arcade library demos.

---

For more information, see:
https://gamedevelopment.tutsplus.com/tutorials/generate-random-cave-levels-using-cellular-automata--gamedev-9664
python -m arcade.examples.procedural_caves_cellular
"""

import random

from ExplorerConfig import ExplorerConfig
from WorldMap import WorldMap


TYPE_NAME = "cellular"

class RandomMap(WorldMap):
    """ Cellular automata based random map """

    def _count_alive_neighbors(self, x: int, y: int) -> int:
        """ Count neighbors that are alive. """
        alive_count = 0
        for i in range(-1, 2):
            for j in range(-1, 2):
                neighbor_x = x + i
                neighbor_y = y + j
                if i == 0 and j == 0:
                    continue
                elif neighbor_x < 0 or neighbor_y < 0 or neighbor_y >= self.rows or neighbor_x >= self.columns:
                    # Edges are considered alive. Makes map more likely to appear naturally closed.
                    alive_count += 1
                elif self.grid[neighbor_y][neighbor_x] == 1:
                    alive_count += 1
        return alive_count

    def _do_simulation_step(self):
        """ Run a step of the cellular automaton. """
        new_grid = self._create_grid()
        cellular_settings = ExplorerConfig().map_generator_settings()['cellular']
        for x in range(self.columns):
            for y in range(self.rows):
                alive_neighbors = self._count_alive_neighbors(x, y)
                if self.grid[y][x] == 1:
                    if alive_neighbors < cellular_settings['death_limit']:
                        new_grid[y][x] = 0
                    else:
                        new_grid[y][x] = 1
                else:
                    if alive_neighbors > cellular_settings['birth_limit']:
                        new_grid[y][x] = 1
                    else:
                        new_grid[y][x] = 0
        self.grid = new_grid

    def _initialize_grid(self):
        """ Randomly set grid locations to on/off based on chance. """
        for c in range(self.columns):
            for r in range(self.rows):
                if random.random() <= ExplorerConfig().map_generator_settings()['cellular']['start_alive_chance']:
                    self.grid[c][r] = 1
        map_generator_settings = ExplorerConfig().map_generator_settings()
        for step in range(map_generator_settings['cellular']['steps']):
            self._do_simulation_step()