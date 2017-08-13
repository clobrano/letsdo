import os
import yaml
from log import info, dbg

class Configuration(object):
    def __init__(self):
        conf_file_path = os.path.expanduser(os.path.join('~', '.letsdo'))
        if os.path.exists(conf_file_path):
            self.configuration = yaml.load(open(conf_file_path).read())

            self.data_dir = self.__get_value('DATADIR')
            if self.data_dir:
                self.data_fullpath = os.path.join(self.data_dir,
                                                  '.letsdo-data')
                self.task_fullpath = os.path.join(self.data_dir,
                                                  '.letsdo-task')
            else:
                info('letsdo data will be saved into HOME directory')
                self.data_fullpath = os.path.expanduser(
                    os.path.join('~', '.letsdo-data'))
                self.task_fullpath = os.path.expanduser(
                    os.path.join('~', '.letsdo-task'))

            if self.__get_value('TODO_FULLPATH'):
                self.todo_fullpath = os.path.expanduser(
                    self.__get_value('TODO_FULLPATH'))
            else:
                self.todo_fullpath = None

            self.todo_start_tag = self.__get_value('TODO_START_TAG')
            self.todo_stop_tag = self.__get_value('TODO_STOP_TAG')

        else:
            dbg('Config file not found. Using default')
            self.data_fullpath = os.path.expanduser(
                os.path.join('~', '.letsdo-data'))
            self.task_fullpath = os.path.expanduser(
                os.path.join('~', '.letsdo-task'))

    def __get_value(self, key):
        try:
            value = os.path.expanduser(self.configuration[key])
        except KeyError as e:
            dbg('configuration: Could not find \'{key}\' field: {msg}'.format(
                key=key, msg=e.message))
            return None
        return value



