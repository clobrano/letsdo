#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Usage:
    letsdo [--force] [--time=<time>] [<name>...]
    letsdo --change <name>...
    letsdo --replace <word>... [--with=<newname>]
    letsdo --to <newtask>...
    letsdo --keep [--id=<id>] [--time=<time>]
    letsdo --stop [--time=<time>]
    letsdo --report [--full] [--daily]
    letsdo --autocomplete

Notes:
    With no arguments, letsdo start a new task or report the status of the current running task

    --to                        Switch to a new task
    -c --change                 Rename current running task
    -k --keep                   Restart last run task
    -i <id> --id=<id>           Task id
    -r --report
    -s --stop                   Stop current running task
    -t <time> --time=<time>     Suggest the start/stop time of the task
    -f --full
    -d --daily
'''

import os
import pickle
import datetime
import time
import docopt
import sys
import logging
import yaml
import re

DATA_FILENAME = ''
TASK_FILENAME = ''

# Logger
level = logging.INFO
logging.basicConfig(level=level, format='  %(message)s')
logger = logging.getLogger(__name__)
info = lambda x: logger.info(x)
err = lambda x: logger.error(x)
warn = lambda x: logger.warn(x)
dbg = lambda x: logger.debug(x)


class Configuration(object):

    def __init__(self):
        conf_file_path = os.path.expanduser(os.path.join('~', '.letsdo'))
        if os.path.exists(conf_file_path):
            configuration = yaml.load(open(conf_file_path).read())
            self.data_filename = os.path.expanduser(os.path.join(configuration['datapath'], '.letsdo-data'))
            self.task_filename = os.path.expanduser(os.path.join(configuration['taskpath'], '.letsdo-task'))
        else:
            dbg('Config file not found. Using default')
            self.data_filename = os.path.expanduser(os.path.join('~', '.letsdo-data'))
            self.task_filename = os.path.expanduser(os.path.join('~', '.letsdo-task'))



class Task(object):
    def __init__(self, name='unknown', start=None, end=None, id=None):
        self.context = None
        self.end_date = None
        self.end_time = None
        self.name = None
        self.start_time = None
        self.tags = None
        self.work_time = None
        self.id = id

        self.parse_name(name.strip())
        if start:
            self.start_time = str2datetime(start.strip()) #datetime.datetime.strptime(start.strip(), '%Y-%m-%d %H:%M')
        else:
            self.start_time = datetime.datetime.now()

        if end:
            self.end_time = str2datetime(end.strip()) #datetime.datetime.strptime(end.strip(), '%Y-%m-%d %H:%M')
            self.end_date = (self.end_time.strftime('%Y-%m-%d'))
            self.work_time = self.end_time - self.start_time

    @staticmethod
    def get():
        TASK_FILENAME = Configuration().task_filename
        if Task.__is_running():
            with open(TASK_FILENAME, 'r') as f:
                return pickle.load(f)

    @staticmethod
    def stop(stop_time_str=None):
        task = Task.get()
        if task:
            stop_time = datetime.datetime.now()
            if stop_time_str:
                stop_time = str2datetime(stop_time_str)
                #stop_time_date = datetime.datetime.strftime(stop_time, '%Y-%m-%d')
                #stop_time = datetime.datetime.strptime(stop_time_date + ' ' + stop_time_str, '%Y-%m-%d %H:%M')

                if stop_time < task.start_time:
                    warn('Given stop time (%s) is more recent than start time (%s)' % (stop_time, task.start_time))
                    return False

            work_time_str = str(stop_time - task.start_time).split('.')[0][:-3]
            status = ('Stopped task \'%s\' after %s of work' % (task.name, work_time_str))
            info(status)

            date = datetime.date.today()
            if task.tags:
                tags = ' '.join(task.tags)
            else:
                tags = None

            start_time_str = str(task.start_time).split('.')[0][:-3]
            stop_time_str = str(stop_time).split('.')[0][:-3]

            report = '%s,%s,%s,%s,%s\n' % (date, task.name, work_time_str, start_time_str, stop_time_str)
            DATA_FILENAME = Configuration().data_filename
            with open(DATA_FILENAME, mode='a') as f:
                f.writelines(report)

            TASK_FILENAME = Configuration().task_filename
            os.remove(TASK_FILENAME)
            return True
        info('No task running')
        return False

    @staticmethod
    def change(name, pattern=None):
        task = Task.get()
        if task:
            if pattern:
                old_name = task.name
                name = old_name.replace(pattern, name)
            info('Renaming task \'%s\' to \'%s\'' % (task.name, name))
            task.parse_name(name)
            return task.__create()

        warn('No task running')

    @staticmethod
    def status():
        task = Task.get()
        if task:
            now = datetime.datetime.now()
            work = str(now - task.start_time).split('.')[0]
            info('Working on \'%s\' for %s' % (task.name, work))
            return True
        else:
            info('No task running')
            return False

    @staticmethod
    def __is_running():
        TASK_FILENAME = Configuration().task_filename
        exists = os.path.exists(TASK_FILENAME)
        dbg('is it running? %d' % exists)
        return exists

    def start(self):
        if not Task.__is_running():
            if self.__create():
                info('Starting task \'%s\'' % self.name)
                return Task.get()

            err('Could not create new task')
            return False

        warn('Another task is running')
        return True

    def __create(self):
        TASK_FILENAME = Configuration().task_filename
        with open(TASK_FILENAME, 'w') as f:
            pickle.dump(self, f)
            return True

    def parse_name(self, name):
        name = name.replace(',', ' ')
        self.name = name
        matches = re.findall('@[\w\-_]+', name)
        if len(matches) == 1:
            self.context = matches[0]
        matches = re.findall('\+[\w\-_]+', name)
        if len(matches) >= 1:
            self.tags = matches

    def __repr__(self):
        work_str = '%s' % str(self.work_time).split('.')[0]
        start_str = '%s' % self.start_time.strftime('%H:%M')
        end_str = '%s' % self.end_time.strftime('%H:%M')
        if self.id is not None:
            return '[%d] - %s| %s (%s -> %s) - %s' % (self.id, self.end_date, work_str, start_str, end_str, self.name)
        return '%s| %s (%s -> %s) - %s' % (self.end_date, work_str, start_str, end_str, self.name)

    def __eq__(self, other):
        return self.name == other.name


def autocomplete():
    message = '''
    Letsdo CLI is able to suggest:
    - command line flags
    - contexts already used (words starting by @ in the task name)
    - tags already used (words starting by + in the task name)

    To enable this feature copy the text after the CUT HERE line into a file and:

        - put the file under /etc/bash_completion.d/ for system-wide autocompletion

    otherwise

        - put the file somewhere in your home directory and source it in your .bashrc
        - source /full/path/to/letsdo_completion

    --- CUT HERE ------------------------------------------------------------------
    '''
    _ROOT = os.path.abspath(os.path.dirname(__file__))
    completion = os.path.join(_ROOT, 'letsdo_scripts', 'letsdo_completion')
    info(message)
    print(open(completion).read())

def str2datetime(string):
    m = re.findall('\d{4}-\d{2}-\d{2} \d{2}:\d{2}', string)
    if len(m) != 0:
        return datetime.datetime.strptime(string, '%Y-%m-%d %H:%M')
    m = re.findall('\d{2}:\d{2}', string)
    if len(m) != 0:
        today_str = datetime.datetime.today().strftime('%Y-%m-%d')
        return datetime.datetime.strptime(today_str + ' ' + string, '%Y-%m-%d %H:%M')
    raise ValueError('Date format not recognized: %s' % string)


def keep(start_time_str=None, id=-1):
    tasks = []
    datafilename = Configuration().data_filename
    with open(datafilename) as f:
        lines = f.readlines()
        try:
            line = lines[id]
        except ValueError:
            if id == -1:
                err('Could not find task last task')
            else:
                err('Could not find task with id %d' % id)
            return

        tok = line.split(',')
        task_name = tok[1]

        if start_time_str:
            date_str = datetime.datetime.strftime(datetime.datetime.today(), '%Y-%m-%d')
            start_time = date_str + ' ' + start_time_str
        else:
            start_time = None

        Task(task_name, start=start_time).start()


def report_task():
    tasks = []
    datafilename = Configuration().data_filename
    with open(datafilename) as f:
        for line in f.readlines():
            tok = line.split(',')
            task = Task(
                    name=tok[1],
                    start=tok[3],
                    end=tok[4])
            try:
                index = tasks.index(task)
                same_task = tasks.pop(index)
                task.work_time += same_task.work_time
            except ValueError:
                pass

            tasks.append(task)

    for idx, task in enumerate(tasks):
        work_str = '%s' % str(task.work_time).split('.')[0]
        info('[%d] %s| %s - %s' % (idx, task.end_date, work_str, task.name))


def report_full(filter=None):
    tasks = {}
    with open(DATA_FILENAME) as f:
        for id, line in enumerate(f.readlines()):
            tok = line.split(',')
            task = Task(
                    name=tok[1],
                    start=tok[3],
                    end=tok[4],
                    id=id)
            date = task.end_date
            if date in tasks.keys():
                tasks[date].append(task)
            else:
                tasks[date] = [task]

        dates = sorted(tasks.keys(), reverse=True)
        for date in dates:
            tot_time = datetime.timedelta()
            column = ''
            for task in tasks[date]:
                tot_time += task.work_time

                work_str = '%s' % str(task.work_time).split('.')[0]
                start_str = '%s' % task.start_time.strftime('%H:%M')
                end_str = '%s' % task.end_time.strftime('%H:%M')

                column += '%s| %s (%s -> %s) - %s' % (task.end_date, work_str, start_str, end_str, task.name)
                column += '\n'

            print('===================================')
            print('%s| Total time: %s' % (date, str(tot_time).split('.')[0]))
            print('-----------------------------------')
            print(column)


def report_daily():
    tasks = {}
    with open(DATA_FILENAME) as f:
        for line in f.readlines():
            tok = line.split(',')
            task = Task(
                    name=tok[1],
                    start=tok[3],
                    end=tok[4]
                    )
            date = task.end_date
            if date in tasks.keys():
                try:
                    index = tasks[date].index(task)
                    same_task = tasks[date][index]
                    same_task.work_time += task.work_time
                except ValueError:
                    tasks[date].append(task)
            else:
                tasks[date] = [task]

    dates = sorted(tasks.keys(), reverse=True)
    for date in dates:
        tot_time = datetime.timedelta()
        column = ''
        for task in tasks[date]:
            tot_time += task.work_time
            work_str = '%s' % str(task.work_time).split('.')[0]
            column += '%s| %s - %s' % (task.end_date, work_str, task.name)
            column += '\n'
        print('===================================')
        print('%s| Total time: %s' % (date, str(tot_time).split('.')[0]))
        print('-----------------------------------')
        print(column)



def main():
    args = docopt.docopt(__doc__)
    dbg(args)

    global DATA_FILENAME
    global TASK_FILENAME
    conf = Configuration()
    DATA_FILENAME = conf.data_filename
    TASK_FILENAME = conf.task_filename

    if args['--stop']:
        Task.stop(args['--time'])
        return

    if args['--change']:
        new_task_name = ' '.join(args['<name>'])
        Task.change(new_task_name)
        return

    if args['--replace']:
        pattern = ' '.join(args['<word>'])
        Task.change(args['--with'], pattern)

    if args['--to']:
        Task.stop()
        new_task_name = ' '.join(args['<newtask>'])
        Task(new_task_name).start()
        return

    if args['--keep']:
        if args['--id']:
            id = eval(args['--id'])
        else:
            id = -1
        keep(start_time_str=args['--time'], id=id)
        return

    if args['--report']:
        if args['--full']:
            report_full()
        elif args['--daily']:
            report_daily()
        else:
            report_task()
        return

    if args['--autocomplete']:
        autocomplete()
        return

    if Task.get():
        Task.status()
        return

    if not args['<name>']:
        args['<name>'] = ['unknown']

        if not args['--force']: # Not sure if asking for status or starting an unnamed task
            resp = raw_input('No running task. Let\'s create a new unnamed one (y/N)?: ')
            if resp.lower() != 'y':
                return

    new_task_name = ' '.join(args['<name>'])
    Task(new_task_name, start=args['--time']).start()


if __name__ == '__main__':
    main()
