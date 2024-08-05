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
