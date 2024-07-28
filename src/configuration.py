"""
This module keeps the classes and function that manage user customization
"""
import os
import yaml
from log import info, LOGGER


CONFIG_FILE_NAME = ".letsdo.yaml"
TASK_FILE_NAME = "letsdo-task"
HISTORY_FILE_NAME = "letsdo-history"


def get_configuration(home="~"):
    """Returns the Yaml configuration"""
    file_path = os.path.join(os.path.expanduser(home), CONFIG_FILE_NAME)
    if not os.path.exists(file_path):
        create_default_configuration(home)
    with open(file_path, "r", encoding="utf-8") as stream:
        return yaml.safe_load(stream)


def create_default_configuration(home="~"):
    default_config = {"color": True, "data_directory": f"{os.path.expanduser(home)}"}
    file_path = os.path.join(os.path.expanduser(home), CONFIG_FILE_NAME)
    with open(file_path, "w") as f:
        return yaml.dump(default_config, f)


def get_task_file_path(home="~"):
    """Return the running task data file path"""
    return os.path.join(get_configuration(home)["data_directory"], TASK_FILE_NAME)


def get_history_file_path(home="~"):
    """Return task history file path"""
    return os.path.join(get_configuration(home)["data_directory"], HISTORY_FILE_NAME)


def autocomplete():
    """Setup autocomplete"""
    message = """
    Letsdo CLI is able to suggest:
    - command line flags
    - contexts already used (words starting by @ in the task name)
    - tags already used (words starting by + in the task name)

    To enable this feature do either of the following:
        - put letsdo_completion file under /etc/bash_completion.d/ for
            system-wide autocompletion
    or:
        - put letsdo_completion file in your home directory and "source" it in
            your .bashrc
        e.g.
            source /full/path/to/letsdo_completion

    Letsdo can copy the script in your $HOME for you if you replay with "Y" at
    this message, otherwise the letsdo_completion file will be printed out here
    and it is up to you to copy and save it as said above.

    Do you want Letsdo to copy the script in your $HOME directory? [Y/n]
    """

    root = os.path.abspath(os.path.dirname(__file__))
    completion = os.path.join(root, "letsdo_scripts", "letsdo_completion")
    if not os.path.exists(completion):
        # probably a snap application.
        LOGGER.warning("could not find completion file")
        return

    info(message)

    resp = input()
    if resp.lower() == "y":
        home_completion = os.path.join(os.path.expanduser("~"), ".letsdo_completion")
        with open(home_completion, "w") as cfile:
            cfile.writelines(open(completion).read())
            if os.path.exists(os.path.join(home_completion)):
                print("completion file installed")
            else:
                print("completion file installation failed: file not found")
    else:
        print("--- CUT HERE ----------------------------------------------------")
        print(open(completion).read())
