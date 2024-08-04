from copy import deepcopy
import yaml

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
        'sim_steps': 1000,
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
            'sensor': {
                'count': 8,
                'beam_grid_scale': 1,
                'range_grid_scale': 5
                },
            'comms': {
                'wireless_range_grid_scale': 5,
                'update_period': 10,
                'resolution': 'parity'
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

class ExplorerConfig:
    def __init__(self, fname=None):
        if not fname is None:
            with open(fname, 'r') as file:
                global hdd_config_file
                hdd_config_file = yaml.safe_load(file)

    def _generic_simple_params(self, key, defaultconfig, config, excluded_keys=[]):
        if not key in defaultconfig:
            raise ValueError(f"\'{key}\' is not a valid config file key")
        params = deepcopy(defaultconfig[key])
        if not config is None and key in config:
            subconfig = config[key]
            for subkey, value in params.items():
                if subkey in excluded_keys:
                    continue
                if subkey in subconfig:
                    params[subkey] = subconfig[subkey]
        return params

    def _simple_params(self, key):
        return self._generic_simple_params(key, DefaultExplorerConfig, hdd_config_file)

    def window_settings(self):
        return self._simple_params('window')

    def drawing_settings(self):
        return self._simple_params('drawing')
 
    def camera_settings(self):
        return self._simple_params('camera')

    def _is_valid_key_chain(self, config, key_chain):
        if config is None:
            return False
        subconfig = deepcopy(config)
        for key in key_chain:
            if key in subconfig:
                subconfig = subconfig[key]
            else:
                return False
        return True

    def bot_count(self):
        if self._is_valid_key_chain(hdd_config_file, ['simulation', 'bot_count']):
            return hdd_config_file['simulation']['bot_count']
        return DefaultExplorerConfig['simulation']['bot_count']

    def sim_steps(self):
        if self._is_valid_key_chain(hdd_config_file, ['simulation', 'sim_steps']):
            return hdd_config_file['simulation']['sim_steps']
        return DefaultExplorerConfig['simulation']['sim_steps']

    def map_generator_settings(self):
        if self._is_valid_key_chain(hdd_config_file, ['simulation']):
            params = self._generic_simple_params('map_generator', DefaultExplorerConfig['simulation'], hdd_config_file['simulation'], ['cellular'])
            params['cellular'] = self._generic_simple_params('cellular', DefaultExplorerConfig['simulation']['map_generator'], hdd_config_file['simulation'])
        else:
            params = deepcopy(DefaultExplorerConfig['simulation']['map_generator'])
        return params

    def robot_sensor_settings(self):
        if self._is_valid_key_chain(hdd_config_file, ['simulation', 'robot']):
            params = self._generic_simple_params('sensor', DefaultExplorerConfig['simulation']['robot'], hdd_config_file['simulation']['robot'])
        else:
            params = deepcopy(DefaultExplorerConfig['simulation']['robot']['sensor'])
        return params

    def robot_comm_settings(self):
        if self._is_valid_key_chain(hdd_config_file, ['simulation', 'robot']):
            params = self._generic_simple_params('comms', DefaultExplorerConfig['simulation']['robot'], hdd_config_file['simulation']['robot'])
        else:
            params = deepcopy(DefaultExplorerConfig['simulation']['robot']['comms'])
        return params

    def robot_name_gen_parameters(self):
        if self._is_valid_key_chain(hdd_config_file, ['simulation', 'robot', 'name_generator']):
            return hdd_config_file['simulation']['robot']['name_generator']
        return deepcopy(DefaultExplorerConfig['simulation']['robot']['name_generator'])

if __name__ == "__main__":
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
    print("robot_sensor_settings:")
    print(default.robot_sensor_settings())
    print("robot_comm_settings:")
    print(default.robot_comm_settings())
    print("robot_name_gen_parameters:")
    print(default.robot_name_gen_parameters())
    print("------------------------------------")
    print("------------------------------------")
    try:
        default._simple_params('invalid_key')
    except ValueError as err:
        print("Attempted invalid key.")
        print("Error message:", err)
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
    print("robot_sensor_settings:")
    print(default.robot_sensor_settings())
    print("robot_comm_settings:")
    print(default.robot_comm_settings())
    print("robot_name_gen_parameters:")
    print(default.robot_name_gen_parameters())