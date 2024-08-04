"""
Heavily based on the demo code. This has a procedurally generated map that is randomly explored by a robot using A*
"""

import arcade

from MainMenu import MainMenuView

# How big the window is
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
WINDOW_TITLE = "Procedural Caves Cellular Automata Example"


def main():
    window = arcade.Window(WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE, resizable=True)
    start_view = MainMenuView()
    window.show_view(start_view)
    arcade.run()


if __name__ == "__main__":
    main()
