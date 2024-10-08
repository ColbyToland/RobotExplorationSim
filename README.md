# RobotExplorationSim
This is meant to be a lightweight Python based simulator to try out robot team map exploration algorithms.

## Setup
> Note: This project is only confirmed to work on Ubuntu 24.04 (Linux)

Basic Python virtual environment setup:

    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt

To save videos you'll also need FFMPEG installed.

## Run
Run the default simulation:

    python3 explorer.py

A custom simulation:

    python3 explorer.py configs/minimal.py

The `configs/base.yaml` should have all adjustable values. In a custom config YAML you don't need all values, just the ones you'd like to override. (Note that `base.yaml` does not represent the default values. It's best to refer to `ExplorerConfig.py` for the default values.)

## Results
The simulation ends with 4 types of output in an `output` directory:

* **`config.yaml`** - a copy of all configuration values for this simulation run
* **`Map - Robot {id}.png`** - occupancy grid per robot
* **`Map - Robot {id} - Merged.png`** - combination of all robot occupancy grids this bot has received and with its own occupancy grid
* **`true_map.png`** - the paths of all robots and all obstructions
* **`statistics.txt`** - any simulation statistics gathered

## New Robot and Map Behavior
To test a new exploration algorithm, create a robot class that inherits from `Robot`. `RandomRobot` gives a basic example. To make it selectable, create a child of `GameView` and override `_is_user_bot` and `_build_user_bot` functions.

For maps, inherit from `WorldMap` and override `_is_user_map` and `_build_user_map` in your `GameView` child class.

## Development
Code quality has been checked with `ruff check`