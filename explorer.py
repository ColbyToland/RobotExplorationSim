"""
Arcade Explorer

A program to simulate simple robots with simple sensors on simple maps. The goal is playing with coordination algorithm.

Heavy usage of Arcade and it's example code as noted in other files. Otherwise originally written by Colby Toland.
"""

import arcade
import argparse
import os
import random

from ExplorerConfig import ExplorerConfig
from MainMenuView import MainMenuView
from SimulationLoggers import setup_sim_logger, SimLogger

# Logging Setup


BASE_NAME = "Arcade Explorer"

def main():
    parser = argparse.ArgumentParser(prog=BASE_NAME,
                                     description="Simulate robots traversing a map with sensors.")
    parser.add_argument('config_filename', nargs='?')
    parser.add_argument('-l', '--log_file', required=False)
    args = parser.parse_args()

    # This is the only place where a config file is passed in. From here, the ExplorerConfig
    # will act like a singleton pattern and continue to use the config file (if one was passed in).
    ExplorerConfig().set_config(args.config_filename)

    # Make sure the output directory exists
    os.makedirs(ExplorerConfig().output_dir(), exist_ok=True)

    # Only need to setup the logger once
    setup_sim_logger(args.log_file)
    logger = SimLogger()
    logger.debug(ExplorerConfig())
    logger.debug("Unrecognized settings:\n" + ExplorerConfig().unrecognized_user_settings_as_str())
    logger.info(f"New simulation started with seed {ExplorerConfig().map_generator_settings()['grid_seed']}")

    # Set random seed if applicable
    random.seed(ExplorerConfig().map_generator_settings()['grid_seed'])

    # Build the window and start the simulation
    window_config = ExplorerConfig().window_settings()
    window_title = BASE_NAME
    if window_config['subtitle']:
        window_title += " " + window_config['subtitle']
    window = arcade.Window(window_config['width'], window_config['height'], window_title, resizable=True)
    start_view = MainMenuView()
    window.show_view(start_view)
    arcade.run()


if __name__ == "__main__":
    main()