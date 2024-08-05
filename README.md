# RobotExplorationSim
This is meant to be a lightweight Python based simulator to try out robot team map exploration algorithms.

## Setup
Basic Python virtual environment setup:

    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt

## Run
Run the default simulation:

    python3 explorer.py

A custom simulation:

    python3 explorer.py configs/minimal.py

The `configs/base.yaml` should have all adjustable values. In a custom config YAML you don't need all values, just the ones you'd like to override. (Note that `base.yaml` does not represent the default values because it's used in testing/validating the config reader.)

## Results
The simulation ends with 4 types of output in an `output` directory:

* **`config.yaml`** - a copy of all configuration values for this simulation run
* **`Map - Robot {id}.png`** - occupancy grid per robot
* **`Map - Robot {id} - Merged.png`** - combination of all robot occupancy grids this bot has received and with its own occupancy grid
* **`true_map.png`** - the paths of all robots and all obstructions
* **`statistics.txt`** - any simulation statistics gathered
