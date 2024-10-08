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

DefaultMapConfigs = {
    'base': {},
    'cellular': {
        'start_alive_chance': 0.4,
        'death_limit': 4,
        'birth_limit': 4,
        'steps': 4
    },
    'manual': {
        'points': [{'x': 0, 'y': 0}],
        'px_not_indices': False
    },
    'image': {
        'image_file': None, # This is invalid!
        'open_cell_color': 'white',
        'custom_color': {'r': 255, 'g':255, 'b':255},
        'scale': 1,
        'ratio': 0, # percent of pixels that aren't the open_cell color to identify an obstruction
        'draw_style': 'obstructions'
    }
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
        'save_video': False,
        'sim_steps': 0,
        'use_async': True,
        'async_physics': True,
        'map_generator': {
            'grid_width': 40,
            'grid_height': 40,
            'grid_seed': None,
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

    def _set_robot_config(self, override_config: dict):
        global hdd_config_file
        global unrecognized_settings
        hdd_config_file['simulation']['robots'] = [deepcopy(DefaultRobotConfig)]
        if is_valid_key_chain(override_config, ['simulation', 'robots']):
            unrecognized_settings.setdefault('simulation', {})['robots'] = []
            hdd_config_file['simulation']['robots'] = [deepcopy(DefaultRobotConfig) for i in range(len(override_config['simulation']['robots']))]

            for i in range(len(override_config['simulation']['robots'])):
                # add defaults for each robot group
                robot_unrecognized_settings = copy_override_dict(hdd_config_file['simulation']['robots'][i], override_config['simulation']['robots'][i])
                if 'type' in override_config['simulation']['robots'][i] and override_config['simulation']['robots'][i]['type'] == 'pc':
                    hdd_config_file['simulation']['robots'][i]['bot_count'] = 1
                unrecognized_settings['simulation']['robots'].append(robot_unrecognized_settings)

    def _set_map_gen_config(self, override_config: dict):
        global hdd_config_file
        global unrecognized_settings
        if is_valid_key_chain(override_config, ['simulation', 'map_generator']):
            for key, defaultconfig in DefaultMapConfigs.items():
                if key in override_config['simulation']['map_generator']:
                    hdd_config_file['simulation']['map_generator'][key] = deepcopy(defaultconfig)
            unrecognized_settings.setdefault('simulation', {})['map_generator'] = copy_override_dict(hdd_config_file['simulation']['map_generator'], override_config['simulation']['map_generator'])
        else:
            hdd_config_file['simulation']['map_generator']['cellular'] = deepcopy(DefaultMapConfigs['cellular'])

    def set_config(self, fname: Optional[str]):
        global hdd_config_file
        global unrecognized_settings
        if hdd_config_file is None:
            hdd_config_file = deepcopy(DefaultExplorerConfig)
        override_config = None
        if fname is not None:
            with open(fname, 'r') as file:
                override_config = yaml.safe_load(file)

                # Setup all settings except the robot groups and map settings
                unrecognized_settings = copy_override_dict(hdd_config_file, override_config)

        # Copy robot settings
        self._set_robot_config(override_config)

        # Copy map generation settings
        self._set_map_gen_config(override_config)

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

    def save_video(self) -> bool:
        return hdd_config_file['simulation']['save_video']

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

    def map_generator_type(self) -> str:
        params = hdd_config_file['simulation']['map_generator']
        for key, defaultconfig in DefaultMapConfigs.items():
            if key in params:
                return key
        return 'base'

    def set_map_grid_width(self, width: int):
        global hdd_config_file
        hdd_config_file['simulation']['map_generator']['grid_width'] = width

    def set_map_grid_height(self, height: int):
        global hdd_config_file
        hdd_config_file['simulation']['map_generator']['grid_height'] = height

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