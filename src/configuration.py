'''
This module keeps the classes and function that manage user customization
'''
import os
import yaml
from log import info, LOGGER


class Configuration(object):
    '''Client customization class'''
    def __init__(self):
        self.conf_file_path = os.path.expanduser(os.path.join('~', '.letsdo'))
        self._todo_file = ''
        self._todo_start_tag = ''
        self._todo_stop_tag = ''

        if os.path.exists(self.conf_file_path):
            self.configuration = yaml.load(open(self.conf_file_path).read())

            self.data_directory = self.__get_value('DATA_DIRECTORY')
            if self.data_directory:
                self.data_fullpath = os.path.join(self.data_directory,
                                                  'letsdo-data')
                self.task_fullpath = os.path.join(self.data_directory,
                                                  'letsdo-task')
            else:
                info('letsdo data will be saved into HOME directory')
                self.data_fullpath = os.path.expanduser(
                    os.path.join('~', '.letsdo-data'))
                self.task_fullpath = os.path.expanduser(
                    os.path.join('~', '.letsdo-task'))

            todo_file = self.__get_value('TODO_FILE')
            if todo_file:
                self.todo_file = os.path.expanduser(todo_file)

                if self.__get_value('TODO_START_TAG'):
                    self.todo_start_tag = self.__get_value('TODO_START_TAG')

                if self.__get_value('TODO_STOP_TAG'):
                    self.todo_stop_tag = self.__get_value('TODO_STOP_TAG')

        else:
            LOGGER.debug('Config file not found. Using defaults')
            self.data_fullpath = os.path.expanduser(
                os.path.join('~', '.letsdo-data'))
            self.task_fullpath = os.path.expanduser(
                os.path.join('~', '.letsdo-task'))

    def __get_value(self, key):
        try:
            value = self.configuration[key]
            if value:
                value = os.path.expanduser(value)
        except KeyError as error:
            LOGGER.debug('could not find key "%s": %s"',
                         key, error)
            return None
        return value

    def __save(self):
        data = {"DATA_DIRECTORY": self.data_directory,
                "TODO_FILE": self.todo_file,
                "TODO_START_TAG": self.todo_start_tag,
                "TODO_STOP_TAG": self.todo_stop_tag}
        with open(self.conf_file_path, 'w') as cfile:
            yaml.dump(data, cfile, default_flow_style=False)

    @property
    def data_directory(self):
        '''returns data directory path'''
        return self._data_directory

    @data_directory.setter
    def data_directory(self, directory):
        if not directory or not os.path.exists(directory):
            LOGGER.error('directory "%s" does not exists', directory)
        else:
            self._data_directory = directory
            self.__save()

    @property
    def todo_file(self):
        '''return todo file path'''
        return self._todo_file

    @todo_file.setter
    def todo_file(self, fullpath):
        if not fullpath or not os.path.exists(fullpath):
            LOGGER.error('file "%s" does not exists', fullpath)
        else:
            self._todo_file = fullpath
            self.__save()

    @property
    def todo_start_tag(self):
        '''return todo start tag'''
        return self._todo_start_tag

    @todo_start_tag.setter
    def todo_start_tag(self, tag):
        self._todo_start_tag = tag
        self.__save()

    @property
    def todo_stop_tag(self):
        '''return todo stop tag'''
        return self._todo_stop_tag

    @todo_stop_tag.setter
    def todo_stop_tag(self, tag):
        self._todo_stop_tag = tag
        self.__save()

    def __repr__(self):
        return "DATA_DIRECTORY: %s\n" \
               "TODO_FILE: %s\n" \
               "TODO_START_TAG: %s\n" \
               "TODO_STOP_TAG: %s" % (self.data_directory,
                                      self.todo_file,
                                      self.todo_start_tag,
                                      self.todo_stop_tag)


def autocomplete():
    '''Setup autocomplete'''
    message = '''
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
    '''

    root = os.path.abspath(os.path.dirname(__file__))
    completion = os.path.join(root, 'letsdo_scripts', 'letsdo_completion')

    info(message)

    resp = input()
    if resp.lower() == 'y':
        completionfile = os.path.join(
            os.path.expanduser(
                '~', ), '.letsdo_completion')
        with open(completionfile, 'w') as cfile:
            cfile.writelines(open(completion).read())
    else:
        print(
            '--- CUT HERE ----------------------------------------------------'
        )
        print(open(completion).read())
