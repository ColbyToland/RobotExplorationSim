"""
Arcade Explorer

A program to simulate simple robots with simple sensors on simple maps. The goal is playing with coordination algorithm.

Heavy usage of Arcade and it's example code as noted in other files. Otherwise originally written by Colby Toland.
"""

import arcade
import argparse
import random

from ExplorerConfig import ExplorerConfig
from MainMenuView import MainMenuView

BASE_NAME = "Arcade Explorer"

def main():
    parser = argparse.ArgumentParser(prog="Arcade Explorer",
                                     description="Simulate robots traversing a map with sensors.")
    parser.add_argument('config_filename', nargs='?')
    args = parser.parse_args()

    # This is the only place where a config file is passed in. From here, the ExplorerConfig
    # will act like a singleton pattern and continue to use the config file (if one was passed in).
    window_config = ExplorerConfig(args.config_filename).window_settings()

    # Set random seed if applicable
    random.seed(ExplorerConfig().map_generator_settings()['grid_seed'])

    # Build the window and start the simulation
    window_title = BASE_NAME
    if window_config['subtitle']:
        window_title += " " + window_config['subtitle']
    window = arcade.Window(window_config['width'], window_config['height'], window_title, resizable=True)
    start_view = MainMenuView()
    window.show_view(start_view)
    arcade.run()


if __name__ == "__main__":
    main()
