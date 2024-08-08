"""
Implement the loggers used throughout the simulation
"""

import logging
from pythonjsonlogger import jsonlogger
import sys
from traceback import print_tb
from typing import Optional

from ExplorerConfig import ExplorerConfig


SIM_LOGGER_NAME = "SimulationLogger"

def setup_logger(logger: logging.Logger, fname: str):
    """ Standardizes logger output style """
    if fname is None:
        raise ValueError("Log file can't be None")
    logHandler = logging.FileHandler(fname)
    jsonFmt = jsonlogger.JsonFormatter(
        "%(name)s %(asctime)s %(levelname)s %(filename)s %(lineno)s %(process)d %(message)s",
        rename_fields={"levelname": "severity", "asctime": "timestamp"},
        datefmt="%Y-%m-%dT%H:%M:%SZ",
    )
    logHandler.setFormatter(jsonFmt)
    logger.addHandler(logHandler)
    logger.setLevel(logging.DEBUG)


def setup_sim_logger(fname: Optional[str]):
    """ Setup the logger for simulation level events """
    setup_logger(SimLogger(), ExplorerConfig().log_file(fname))

    sys.excepthook = handle_exception

def SimLogger() -> logging.Logger:
    return logging.getLogger(SIM_LOGGER_NAME)

def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    SimLogger().critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

    print("Traceback:")
    print_tb(exc_traceback)
    print(exc_type.__name__ + ": " + str(exc_value))


logging_robot_count = 0

def setup_robot_logger():
    """ Setup the logger for a single robot

    Let the config file switch between using the simulation wide logger and a per-bot logger.
    """
    logger_id = SIM_LOGGER_NAME
    if ExplorerConfig().split_out_bot_logs():
        global logging_robot_count
        logger_id = "Robot " + str(logging_robot_count)
        logging_robot_count += 1
        logger = logging.getLogger(logger_id)
        fname = ExplorerConfig().output_dir() + "/" + logger_id + ".log"
        setup_logger(logger, fname)
    return logger_id

def RobotLogger(robot_id) -> logging.Logger:
    return logging.getLogger(robot_id)