'''
This module keeps the classes and function that manage user customization
'''
import os
import yaml
from log import info, LOGGER


class Configuration(object):
    '''Client customization class'''
    def __init__(self):
        self._data_directory = os.path.expanduser('~')

        self.conf_file_path = os.path.join(os.path.expanduser('~'), '.letsdo')
        if not os.path.exists(self.conf_file_path):
            LOGGER.debug('creating config file "%s".', self.conf_file_path)
            self.__save()

        self.configuration = yaml.load(open(self.conf_file_path).read())
        self.data_directory = os.path.expanduser(self.__get_value('DATA_DIRECTORY'))

        if not self.data_directory or not os.path.exists(self.data_directory):
            LOGGER.fatal("could not save task data in %s", self.data_directory)
        else:
            self.data_fullpath = os.path.join(self.data_directory, 'letsdo-data')
            self.task_fullpath = os.path.join(self.data_directory, 'letsdo-task')

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
        data = {"DATA_DIRECTORY": self.data_directory}
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
            return

        self._data_directory = directory
        self.__save()

    def __repr__(self):
        return "DATA_DIRECTORY: %s\n" % (self.data_directory)


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
    if not os.path.exists(completion):
        # probably a snap application.
        LOGGER.warning("could not find completion file")
        return

    info(message)

    resp = input()
    if resp.lower() == 'y':
        home_completion = os.path.join(os.path.expanduser('~'), '.letsdo_completion')
        with open(home_completion, 'w') as cfile:
            cfile.writelines(open(completion).read())
            if os.path.exists(os.path.join(home_completion)):
                print('completion file installed')
            else:
                print('completion file installation failed: file not found')
    else:
        print(
            '--- CUT HERE ----------------------------------------------------'
        )
        print(open(completion).read())
