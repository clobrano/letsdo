'''
This module keeps the classes and function that manage user customization
'''
import os
import yaml
from log import info, err, dbg


class Configuration(object):
    '''Client customization class'''
    def __init__(self):
        self.conf_file_path = os.path.expanduser(os.path.join('~', '.letsdo'))
        self._todo_fullpath = ''
        self._todo_start_tag = ''
        self._todo_stop_tag = ''

        if os.path.exists(self.conf_file_path):
            self.configuration = yaml.load(open(self.conf_file_path).read())

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

            todo_fullpath = self.__get_value('TODO_FULLPATH')
            if todo_fullpath:
                self.todo_fullpath = os.path.expanduser(todo_fullpath)

                if self.__get_value('TODO_START_TAG'):
                    self.todo_start_tag = self.__get_value('TODO_START_TAG')

                if self.__get_value('TODO_STOP_TAG'):
                    self.todo_stop_tag = self.__get_value('TODO_STOP_TAG')

        else:
            dbg('Config file not found. Using defaults')
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

    def __save(self):
        data = {
            "DATADIR": self.data_dir,
            "TODO_FULLPATH": self.todo_fullpath,
            "TODO_START_TAG": self.todo_start_tag,
            "TODO_STOP_TAG": self.todo_stop_tag
                }
        with open(self.conf_file_path, 'w') as cfile:
            yaml.dump(data, cfile, default_flow_style=False)

    @property
    def data_dir(self):
        return self._data_dir

    @data_dir.setter
    def data_dir(self, directory):
        if not directory or not os.path.exists(directory):
            err('directory "{dir}" does not exists'.format(dir=directory))
        else:
            self._data_dir = directory
            self.__save()

    @property
    def todo_fullpath(self):
        return self._todo_fullpath

    @todo_fullpath.setter
    def todo_fullpath(self, fullpath):
        if not fullpath or not os.path.exists(fullpath):
            err('file "{file}" does not exists'.format(file=fullpath))
        else:
            self._todo_fullpath = fullpath
            self.__save()

    @property
    def todo_start_tag(self):
        return self._todo_start_tag

    @todo_start_tag.setter
    def todo_start_tag(self, tag):
        self._todo_start_tag = tag
        self.__save()

    @property
    def todo_stop_tag(self):
        return self._todo_stop_tag

    @todo_stop_tag.setter
    def todo_stop_tag(self, tag):
        self._todo_stop_tag = tag
        self.__save()


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

    resp = raw_input()
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


def do_config(args):
    if args['data.directory']:
        Configuration().data_dir = args['<fullpath>']

    elif args['todo.file']:
        Configuration().todo_fullpath = args['<fullpath>']

    elif args['todo.start']:
        Configuration().todo_start_tag = args['<tag>']

    elif args['todo.stop']:
        Configuration().todo_stop_tag = args['<tag>']

    elif args['autocomplete']:
        autocomplete()
    else:
        pass
