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

from OccupancyGrid import GridResolution


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
        'bot_count': 3,
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
        'robot': {
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
        }
    }

hdd_config_file = None

def copy_override_dict(main_dict, override_dict):
    """ Recursive copying of override values from one dict to another """
    if override_dict is None:
        return
    for key, value in override_dict.items():
        if key in main_dict:
            if isinstance(value, dict):
                copy_override_dict(main_dict[key], override_dict[key])
            else:
                main_dict[key] = override_dict[key]

def is_valid_key_chain(config, key_chain):
    if config is None:
        return False
    subconfig = deepcopy(config)
    for key in key_chain:
        if key in subconfig:
            subconfig = subconfig[key]
        else:
            return False
    return True

class ExplorerConfig:
    def __init__(self, fname=None):
        global hdd_config_file
        if hdd_config_file is None:
            hdd_config_file = deepcopy(DefaultExplorerConfig)
        if not fname is None:
            with open(fname, 'r') as file:
                override_config = yaml.safe_load(file)
                if is_valid_key_chain(override_config, ['simulation', 'map_generator', 'grid_seed']) and override_config['simulation']['map_generator']['grid_seed']:
                    # If there is a random seed in the config file then default async_physics off
                    hdd_config_file['simulation']['async_physics'] = False
                copy_override_dict(hdd_config_file, override_config)

    def window_settings(self):
        return hdd_config_file['window']

    def drawing_settings(self):
        return hdd_config_file['drawing']
 
    def camera_settings(self):
        return hdd_config_file['camera']

    def bot_count(self):
        return hdd_config_file['simulation']['bot_count']

    def sim_steps(self):
        return hdd_config_file['simulation']['sim_steps']

    def async_params(self):
        return {'use_async': hdd_config_file['simulation']['use_async'], 
                'async_physics': hdd_config_file['simulation']['async_physics']}

    def map_generator_settings(self):
        params = deepcopy(hdd_config_file['simulation']['map_generator'])
        if params['grid_seed'] is None:
            # Set a random seed to the random library and store it so we can reproduce this run in the future
            hdd_config_file['simulation']['map_generator']['grid_seed'] = random.randrange(sys.maxsize)
            params['grid_seed'] = hdd_config_file['simulation']['map_generator']['grid_seed']
        return params

    def robot_type(self):
        return hdd_config_file['simulation']['robot']['type']

    def robot_map_resolution(self):
        rez_name =  hdd_config_file['simulation']['robot']['map_resolution'].casefold().strip()
        if rez_name == 'parity':
            return GridResolution.PARITY
        elif rez_name == 'low':
            return GridResolution.LOW
        elif rez_name == 'high':
            return GridResolution.HIGH
        raise ValueError(f"Invalid resolution type: {rez_name}")

    def robot_sensor_settings(self):
        return deepcopy(hdd_config_file['simulation']['robot']['sensor'])

    def robot_comm_settings(self):
        return deepcopy(hdd_config_file['simulation']['robot']['comms'])

    def robot_name_gen_parameters(self):
        return deepcopy(hdd_config_file['simulation']['robot']['name_generator'])

    def __str__(self):
        return yaml.dump(deepcopy(hdd_config_file))

if __name__ == "__main__":
    # TODO: Convert this to a unit test in pytest!

    print("No file just defaults:")
    print("======================")
    default = ExplorerConfig()
    print("window_settings:")
    print(default.window_settings())
    print("drawing_settings")
    print(default.drawing_settings())
    print("camera_settings:")
    print(default.camera_settings())
    print("bot_count:")
    print(default.bot_count())
    print("sim_steps:")
    print(default.sim_steps())
    print("map_generator_settings:")
    print(default.map_generator_settings())
    print("robot_map_resolution:")
    print(default.robot_map_resolution())
    print("robot_sensor_settings:")
    print(default.robot_sensor_settings())
    print("robot_comm_settings:")
    print(default.robot_comm_settings())
    print("robot_name_gen_parameters:")
    print(default.robot_name_gen_parameters())
    print("------------------------------------")
    print("------------------------------------")
    print("base.yaml:")
    print("==========")
    ExplorerConfig("configs/base.yaml")
    print("window_settings:")
    print(default.window_settings())
    print("drawing_settings")
    print(default.drawing_settings())
    print("camera_settings:")
    print(default.camera_settings())
    print("bot_count:")
    print(default.bot_count())
    print("sim_steps:")
    print(default.sim_steps())
    print("map_generator_settings:")
    print(default.map_generator_settings())
    print("robot_map_resolution:")
    print(default.robot_map_resolution())
    print("robot_sensor_settings:")
    print(default.robot_sensor_settings())
    print("robot_comm_settings:")
    print(default.robot_comm_settings())
    print("robot_name_gen_parameters:")
    print(default.robot_name_gen_parameters())
    print("------------------------------------")
    print("------------------------------------")
    print("minimal.yaml:")
    print("=============")
    ExplorerConfig("configs/minimal.yaml")
    print("window_settings:")
    print(default.window_settings())
    print("drawing_settings")
    print(default.drawing_settings())
    print("camera_settings:")
    print(default.camera_settings())
    print("bot_count:")
    print(default.bot_count())
    print("sim_steps:")
    print(default.sim_steps())
    print("map_generator_settings:")
    print(default.map_generator_settings())
    print("robot_map_resolution:")
    print(default.robot_map_resolution())
    print("robot_sensor_settings:")
    print(default.robot_sensor_settings())
    print("robot_comm_settings:")
    print(default.robot_comm_settings())
    print("robot_name_gen_parameters:")
    print(default.robot_name_gen_parameters())