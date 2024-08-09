"""
Configuration Manager

This includes both the default configuration values and a reader for YAML config files.

Config files are overrides from the default so they can be just a subset of settings.

Unfortunately, this does not enforce data types so bad config files could do weird things.
This is considered user error not a bug.

Comments to what each parameter does are in configs/base.yaml
"""

from copy import deepcopy
import random
import sys
import yaml

from OccupancyGridTypes import GridResolution
from typing import Optional
from utils import copy_override_dict, is_valid_key_chain


DefaultRobotConfig = {
    'bot_count': 3,
    'type': 'random',
    'map_resolution': 'parity',
    'sensor': {
        'count': 8,
        'beam_grid_scale': 1,
        'range_grid_scale': 5
        },
    'comms': {
        'wireless_range_grid_scale': 5,
        'update_period': 10,
        },
    'name_generator': [
            [
            'Red',
            'Green',
            'Blue',
            'Black',
            'White',
            'Gold',
            'Silver'
            ],
            [
            'Wolf',
            'Dragon',
            'Falcon',
            'Viper',
            'Shark',
            'Hornet'
            ]
        ]
    }

DefaultExplorerConfig = {
    'window': {
        'width': 800,
        'height': 600,
        'subtitle': ''
        },
    'drawing':{
        'scale': 0.125,
        'size': 128,
        'draw_trajectory': True,
        'draw_sensors': True,
        'draw_comms': True
        },
    'camera': {
        'viewport_margin': 300,
        'speed': 0.1,
        'focus_timer': 200
        },
    'simulation': {
        'output_dir': 'output',
        'log_file': 'simulation.log',
        'split_out_bot_logs': False,
        'sim_steps': 200,
        'use_async': True,
        'async_physics': True,
        'map_generator': {
            'grid_width': 40,
            'grid_height': 40,
            'grid_seed': None,
            'cellular': {
                'start_alive_chance': 0.4,
                'death_limit': 4,
                'birth_limit': 4,
                'steps': 4
                }
            },
        'robots': []
        }
    }

hdd_config_file = None
unrecognized_settings = {}

class ExplorerConfig:
    def __init__(self):
        global hdd_config_file
        if hdd_config_file is None:
            hdd_config_file = deepcopy(DefaultExplorerConfig)

    def set_config(self, fname: Optional[str]):
        global hdd_config_file
        global unrecognized_settings
        if hdd_config_file is None:
            hdd_config_file = deepcopy(DefaultExplorerConfig)
        if fname is not None:
            with open(fname, 'r') as file:
                override_config = yaml.safe_load(file)

                if is_valid_key_chain(override_config, ['simulation', 'map_generator', 'grid_seed']) and override_config['simulation']['map_generator']['grid_seed']:
                    # If there is a random seed in the config file then default async_physics off
                    # Do this before the override copy so the user config still overrides this
                    hdd_config_file['simulation']['async_physics'] = False

                # Setup all settings except the robot groups
                unrecognized_settings = copy_override_dict(hdd_config_file, override_config)

                # Copy robot settings
                hdd_config_file['simulation']['robots'] = [deepcopy(DefaultRobotConfig)]
                if is_valid_key_chain(override_config, ['simulation', 'robots']):
                    unrecognized_settings.setdefault('simulation', {})['robots'] = []
                    hdd_config_file['simulation']['robots'] = [deepcopy(DefaultRobotConfig) for i in range(len(override_config['simulation']['robots']))]

                    for i in range(len(override_config['simulation']['robots'])):
                        # add defaults for each robot group
                        robot_unrecognized_settings = copy_override_dict(hdd_config_file['simulation']['robots'][i], override_config['simulation']['robots'][i])
                        unrecognized_settings['simulation']['robots'].append(robot_unrecognized_settings)

    def unrecognized_user_settings(self) -> dict:
        return unrecognized_settings

    def unrecognized_user_settings_as_str(self) -> str:
        return yaml.dump(deepcopy(unrecognized_settings))

    def window_settings(self) -> dict:
        return hdd_config_file['window']

    def drawing_settings(self) -> dict:
        return hdd_config_file['drawing']

    def grid_size(self) -> float:
        drawing_settings = self.drawing_settings()
        return drawing_settings['size']*drawing_settings['scale']
 
    def camera_settings(self) -> dict:
        return hdd_config_file['camera']

    def output_dir(self) -> str:
        return hdd_config_file['simulation']['output_dir']

    def log_file(self, fname: Optional[str]=None) -> str:
        if fname is not None:
            # Set it here in case another class wants to create additional logs based on the main log name
            hdd_config_file['simulation']['log_file'] = fname
        return hdd_config_file['simulation']['output_dir'] + "/" + hdd_config_file['simulation']['log_file']

    def split_out_bot_logs(self) -> bool:
        return hdd_config_file['simulation']['split_out_bot_logs']

    def sim_steps(self) -> int:
        return hdd_config_file['simulation']['sim_steps']

    def async_params(self) -> dict:
        return {'use_async': hdd_config_file['simulation']['use_async'], 
                'async_physics': hdd_config_file['simulation']['async_physics']}

    def map_generator_settings(self) -> dict:
        params = deepcopy(hdd_config_file['simulation']['map_generator'])
        if params['grid_seed'] is None:
            # Set a random seed to the random library and store it so we can reproduce this run in the future
            hdd_config_file['simulation']['map_generator']['grid_seed'] = random.randrange(sys.maxsize)
            params['grid_seed'] = hdd_config_file['simulation']['map_generator']['grid_seed']
        return params

    def max_x(self) -> int:
        return int(self.map_generator_settings()['grid_width'] * self.grid_size())

    def max_y(self) -> int:
        return int(self.map_generator_settings()['grid_height'] * self.grid_size())

    def total_bot_count(self) -> int:
        total = 0
        for robot_group in hdd_config_file['simulation']['robots']:
            total += robot_group['bot_count']
        return total

    def robot_group_count(self) -> int:
        return len(hdd_config_file['simulation']['robots'])

    def bot_count(self, robot_group_id: int) -> int:
        return hdd_config_file['simulation']['robots'][robot_group_id]['bot_count']

    def robot_type(self, robot_group_id: int) -> str:
        return hdd_config_file['simulation']['robots'][robot_group_id]['type']

    def robot_map_resolution(self, robot_group_id: int) -> GridResolution:
        if 'map_resolution' not in hdd_config_file['simulation']['robots'][robot_group_id]:
            # Don't use an occupancy grid
            return GridResolution.NONE
        rez_name = hdd_config_file['simulation']['robots'][robot_group_id]['map_resolution'].casefold().strip()
        if rez_name == 'parity':
            return GridResolution.PARITY
        elif rez_name == 'low':
            return GridResolution.LOW
        elif rez_name == 'high':
            return GridResolution.HIGH
        raise ValueError(f"Invalid resolution type: {rez_name}")

    def robot_sensor_settings(self, robot_group_id: int) -> dict:
        return deepcopy(hdd_config_file['simulation']['robots'][robot_group_id]['sensor'])

    def robot_comm_settings(self, robot_group_id: int) -> dict:
        return deepcopy(hdd_config_file['simulation']['robots'][robot_group_id]['comms'])

    def robot_name_gen_parameters(self, robot_group_id: int) -> list[list[str]]:
        return deepcopy(hdd_config_file['simulation']['robots'][robot_group_id]['name_generator'])

    def __str__(self) -> str:
        return yaml.dump(deepcopy(hdd_config_file))