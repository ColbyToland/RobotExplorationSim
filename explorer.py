import arcade
import argparse

from ExplorerConfig import ExplorerConfig
from MainMenuView import MainMenuView

BASE_NAME = "Arcade Explorer"

def main():
    parser = argparse.ArgumentParser(prog="Arcade Explorer",
                                     description="Simulate robots traversing a map with sensors.")

    parser.add_argument('config_filename')
    args = parser.parse_args()

    window_config = ExplorerConfig(args.config_filename).window_settings()
    window = arcade.Window(window_config['width'], window_config['height'], BASE_NAME + window_config['subtitle'], resizable=True)
    start_view = MainMenuView()
    window.show_view(start_view)
    arcade.run()


if __name__ == "__main__":
    main()
