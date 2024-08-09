"""
Occupancy Grid shared data types
"""

from enum import Enum


class GridResolution(Enum):
    """ Setting to adjsut the model vs real world map complexity """
    NONE = -1
    LOW = 0
    PARITY = 1
    HIGH = 2


class GridCellStatus(Enum):
    """ Summary description of a cell status """
    UNEXPLORED = -1
    CLEAR = 0
    OBSTACLE = 1


# Should this be in the config file? Seems algorithm dependent so opted for simplicity.
DEFAULT_OBSTACLE_THRESHOLD = 0.5

class GridCell:
    """ A single cell of the occupancy grid """

    def __init__(self):
        """ default to UNEXPLORED_CELL """
        self._obstacles = -1
        self._observations = -1

    def _observe(self):
        """ Transition out of UNEXPLORED state """
        if self.status() == GridCellStatus.UNEXPLORED:
            self._obstacles = 0
            self._observations = 0

    def observe(self):
        """ Increment the observations for this cell """
        self._observe()
        self._observations += 1

    def observe_obstacle(self):
        """ Increment the observations and obstacle observations for this cell """
        self.observe()
        self._obstacles += 1

    def status(self, obstacle_threshold=DEFAULT_OBSTACLE_THRESHOLD):
        """ Convert the obstacle/observation ratio to a state

        obstacle_threshold -- Define the minimum % obstacle observations to be considered an obstacle
        """
        if self._observations == -1:
            return GridCellStatus.UNEXPLORED
        pct = self._obstacles / self._observations
        if pct > obstacle_threshold:
            return GridCellStatus.OBSTACLE 
        return GridCellStatus.CLEAR

    def copy(self):
        """ Create an identical GridCell """
        mirror = GridCell()
        mirror._obstacles = self._obstacles
        mirror._observations = self._observations
        assert self == mirror
        return mirror


    # Math and logic operations
    
    def __iadd__(self, cell):
        if cell.status() != GridCellStatus.UNEXPLORED:
            self._observe()
            self._observations += cell._observations
            self._obstacles += cell._obstacles
        return self

    def __eq__(self, other):
        return self._obstacles == other._obstacles and self._observations == other._observations

    def __ne__(self, other):
        return not self.__eq__(other)