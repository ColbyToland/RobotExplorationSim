"""
Heavily based on the demo code. This has a procedurally generated map that is randomly explored by a robot using A*
"""

import arcade

from ExplorerConfig import ExplorerConfig
from MainMenuView import MainMenuView


def main():
    window_config = ExplorerConfig().window_settings()
    window = arcade.Window(window_config['width'], window_config['height'], "Arcade Explorer" + window_config['subtitle'], resizable=True)
    start_view = MainMenuView()
    window.show_view(start_view)
    arcade.run()


if __name__ == "__main__":
    main()
