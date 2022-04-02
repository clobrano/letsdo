"""
This module manages user customization
"""
from typing import Dict
from os.path import expanduser, join
import yaml

CONFIG_FILE_NAME: str = ".letsdo"
CONFIG_COLOR_ENABLED_DEFAULT: bool = True
CONFIG_DATA_DIRECTORY_DEFAULT: str = "~"
CONFIG_DATA_FILENAME: str = "letsdo-data"
CONFIG_TASK_FILENAME: str = "letsdo-task"


def load(home: str = "~") -> Dict[str, str]:
    """
    Load configuration data from user HOME directory
    """

    conf_file_path = join(expanduser(home), CONFIG_FILE_NAME)
    config = yaml.safe_load(open(conf_file_path).read())

    config["COLOR_ENABLED"] = config.get(
            "COLOR_ENABLED", CONFIG_COLOR_ENABLED_DEFAULT)

    config["DATA_DIRECTORY"] = config.get(
            "DATA_DIRECTORY", CONFIG_DATA_DIRECTORY_DEFAULT)
    return config


def save(data: Dict[str, str], home: str = "~") -> None:
    conf_file_path = join(expanduser(home), CONFIG_FILE_NAME)
    with open(conf_file_path, "w") as f:
        yaml.dump(data, f, default_flow_style=False)


def data_fullpath(data: Dict[str, str]) -> str:
    return join(data["DATA_DIRECTORY"], CONFIG_DATA_FILENAME)


def task_fullpath(data: Dict[str, str]) -> str:
    return join(data["DATA_DIRECTORY"], CONFIG_TASK_FILENAME)
