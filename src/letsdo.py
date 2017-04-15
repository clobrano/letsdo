#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Usage:
    letsdo [--time=<time>] [--keep=<id>|<name>...]
    letsdo --change <name>...
    letsdo --replace=<target>... --with=<string>...
    letsdo --to <newtask>...
    letsdo --stop [--time=<time>]
    letsdo --report [--all] [--yesterday] [<filter>]
    letsdo --report --full [--all] [--yesterday] [<filter>]
    letsdo --report --daily [--all] [--yesterday] [<filter>]
    letsdo --autocomplete

options:
    -a --all                    Report activities for all stored days
    --to                        Stop current task and switch to a new one
    -c --change                 Rename current task
    -d --daily                  Report today activities by task
    --debug                     Enable debug logs
    -f --full                   Report today full activity with start/end time
    -k <id> --keep=<id>         Restart last run task (default: 0)
    -r --report                 Report whole time spent on each task
    -s --stop                   Stop current running task
    -t <time> --time=<time>     Suggest the start/stop time of the task
    -y --yesterday              Fast switch to show reports of the day before
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
            try:
                self.data_filename = os.path.expanduser(os.path.join(configuration['datapath'], '.letsdo-data'))
            except KeyError as e:
                err('Config file error: Could not find \'{msg}\' field'.format(msg=e.message))
                self.data_filename = os.path.expanduser(os.path.join('~', '.letsdo-data'))

            try:
                self.task_filename = os.path.expanduser(os.path.join(configuration['taskpath'], '.letsdo-task'))
            except KeyError as e:
                err('Config file error: Could not find \'{msg}\' field'.format(msg=e.message))
                self.task_filename = os.path.expanduser(os.path.join('~', '.letsdo-data'))

            dbg('Configuration: data filename {file}'.format(file = self.data_filename))
            dbg('Configuration: task filename {file}'.format(file = self.task_filename))
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
        self.work_time = datetime.timedelta()
        self.id = id
        self.pause = 0

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
    def get_running():
        TASK_FILENAME = Configuration().task_filename
        if Task.__is_running():
            with open(TASK_FILENAME, 'r') as f:
                return pickle.load(f)
        return None

    @staticmethod
    def stop(stop_time_str=None):
        task = Task.get_running()
        if not task:
            info('No task running')
            return

        if stop_time_str:
            stop_time = str2datetime(stop_time_str)
            if stop_time < task.start_time:
                warn('Given stop time (%s) is more recent than start time (%s)' % (stop_time, task.start_time))
                return False
            date = stop_time.strftime('%Y-%m-%d')
        else:
            stop_time = datetime.datetime.now()
            date = datetime.date.today()

        work_time_str = str(stop_time - task.start_time).split('.')[0][:-3]
        start_time_str = str(task.start_time).split('.')[0][:-3]
        stop_time_str = str(stop_time).split('.')[0][:-3]

        report = '%s,%s,%s,%s,%s\n' % (date, task.name, work_time_str, start_time_str, stop_time_str)
        DATA_FILENAME = Configuration().data_filename
        with open(DATA_FILENAME, mode='a') as f:
            f.writelines(report)

        TASK_FILENAME = Configuration().task_filename
        os.remove(TASK_FILENAME)
        status = ('Stopped task \'%s\' after %s of work' % (task.name, work_time_str))
        info(status)
        return True

    @staticmethod
    def change(name, pattern=None):
        task = Task.get_running()
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
        task = Task.get_running()
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
                return Task.get_running()

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

    def __ne__(self, other):
        return not (self.name == other.name)

    def __hash__(self):
        return hash((self.name))


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

def format_h_m(string):
    return ':'.join(string.split(':')[0:2])

def str2datetime(string):
    m = re.findall('\d{4}-\d{2}-\d{2} \d{2}:\d{2}', string)
    if len(m) != 0:
        string = m[0]
        return datetime.datetime.strptime(string, '%Y-%m-%d %H:%M')

    m = re.findall('\d{4}-\d{2}-\d{2} \d{2}.\d{2}', string)
    if len(m) != 0:
        string = m[0]
        return datetime.datetime.strptime(string, '%Y-%m-%d %H.%M')

    m = re.findall('\d{4}/\d{2}/\d{2} \d{2}:\d{2}', string)
    if len(m) != 0:
        string = m[0]
        return datetime.datetime.strptime(string, '%Y/%m/%d %H:%M')

    m = re.findall('\d{4}/\d{2}/\d{2} \d{2}.\d{2}', string)
    if len(m) != 0:
        string = m[0]
        return datetime.datetime.strptime(string, '%Y/%m/%d %H.%M')

    m = re.findall('\d{4}-\d{2}-\d{2}', string)
    if len(m) != 0:
        string = m[0]
        now_str = datetime.datetime.now().strftime('%H:%M')
        return datetime.datetime.strptime(string + ' ' + now_str, '%Y-%m-%d %H:%M')

    m = re.findall('\d{4}/\d{2}/\d{2}', string)
    if len(m) != 0:
        string = m[0]
        now_str = datetime.datetime.now().strftime('%H:%M')
        return datetime.datetime.strptime(string + ' ' + now_str, '%Y/%m/%d %H:%M')

    m = re.findall('\d{2}-\d{2} \d{2}:\d{2}', string)
    if len(m) != 0:
        string = m[0]
        year_str = datetime.datetime.today().strftime('%Y')
        return datetime.datetime.strptime(year_str + '-' + string, '%Y-%m-%d %H:%M')

    m = re.findall('\d{2}-\d{2} \d{2}.\d{2}', string)
    if len(m) != 0:
        string = m[0]
        year_str = datetime.datetime.today().strftime('%Y')
        return datetime.datetime.strptime(year_str + '-' + string, '%Y-%m-%d %H:%M')

    m = re.findall('\d{2}-\d{2}', string)
    if len(m) != 0:
        string = m[0]
        year_str = datetime.datetime.today().strftime('%Y')
        now_str = datetime.datetime.now().strftime('%H:%M')
        return datetime.datetime.strptime(year_str + '-' + string + ' ' + now_str, '%Y-%m-%d %H:%M')

    m = re.findall('\d{2}:\d{2}', string)
    if len(m) != 0:
        string = m[0]
        today_str = datetime.datetime.today().strftime('%Y-%m-%d')
        return datetime.datetime.strptime(today_str + ' ' + string, '%Y-%m-%d %H:%M')

    m = re.findall('\d:\d{2}', string)
    if len(m) != 0:
        string = m[0]
        today_str = datetime.datetime.today().strftime('%Y-%m-%d')
        return datetime.datetime.strptime(today_str + ' ' + string, '%Y-%m-%d %H:%M')

    m = re.findall('\d{2}.\d{2}', string)
    if len(m) != 0:
        string = m[0]
        today_str = datetime.datetime.today().strftime('%Y-%m-%d')
        return datetime.datetime.strptime(today_str + ' ' + string, '%Y-%m-%d %H.%M')

    m = re.findall('\d.\d{2}', string)
    if len(m) != 0:
        string = m[0]
        today_str = datetime.datetime.today().strftime('%Y-%m-%d')
        return datetime.datetime.strptime(today_str + ' ' + string, '%Y-%m-%d %H.%M')


    raise ValueError('Date format not recognized: %s' % string)


def keep(start_time_str=None, id=-1):
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

        if id >= 0:
            tasks.reverse()

        task_name = tasks[id].name

        if start_time_str:
            date_str = datetime.datetime.strftime(datetime.datetime.today(), '%Y-%m-%d')
            start_time = date_str + ' ' + start_time_str
        else:
            start_time = None

        Task(task_name, start=start_time).start()


def get_tasks(condition=None):
    tasks = []
    datafilename = Configuration().data_filename
    id = -1
    try:
        with open(datafilename) as f:
            for line in reversed(f.readlines()):
                dbg(line)
                fields = line.strip().split(',')
                t = Task(name=fields[1],
                         start=fields[3],
                         end=fields[4])
                try:
                    same_task = tasks.index(t)
                    t.id = tasks[same_task].id
                    dbg('{task_name} has old id {id}'.format(task_name=t.name, id=t.id))
                except ValueError:
                    id +=1
                    t.id = id
                    dbg('{task_name} has new id {id}'.format(task_name=t.name, id=t.id))
                tasks.append(t)

        return filter(condition, tasks)
    except IOError:
        return []


def group_task_by(tasks, group=None):
    groups = []
    if group is 'task':
        uniques = []
        for task in tasks:
            if not task in uniques:
                uniques.append(task)

        for main_task in uniques:
            work_time_in_seconds = sum([same_task.work_time.seconds for same_task in tasks if same_task == main_task])
            work_time = datetime.timedelta(seconds=work_time_in_seconds)
            main_task.work_time = work_time
        return uniques

    elif group is 'date':
        map = {}
        for t in tasks:
            date = t.end_date
            if date in map.keys():
                map[date].append(t)
            else:
                map[date] = [t]
        return map
    else:
        return tasks


def report_task(tasks, filter=None):
    tot_work_time = datetime.timedelta()
    info('#ID  |      Worked         | task name')
    info('----------------------------------------')
    for task in tasks:
        tot_work_time += task.work_time
        info('#{id:03d} | {lasttime} {worked:>8s} | {name}'.format(id=task.id,
            worked=format_h_m(str(task.work_time)),
            name=task.name,
            lasttime=task.end_date))
    info('----------------------------------------')
    if filter:
        info('{filter}: Total work time {time}'.format(filter=filter, time=format_h_m(str(tot_work_time))))
    else:
        info('Total work time {time}'.format(filter=filter, time=format_h_m(str(tot_work_time))))
    info('')


def report_full(filter=None):
    tasks = {}
    datafilename = Configuration().data_filename
    with open(datafilename) as f:
        for id, line in enumerate(f.readlines()):
            line = line.strip()
            tok = line.split(',')
            if not filter or (filter in tok[4] or filter in tok[1]):
                dbg('accepting %s' % line)
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

        if len(tasks) == 0:
            info('No tasks found with filter \'{filter}\''.format(filter=filter))
            return

        dates = sorted(tasks.keys(), reverse=True)
        for date in dates:
            column = ''
            tot_time = datetime.timedelta()
            pause_start = None
            pause_stop = None
            pause = datetime.timedelta()
            for task in tasks[date]:
                # Computing pause time
                if pause_start is not None:
                    pause_stop = task.start_time
                    pause += pause_stop - pause_start
                pause_start = task.end_time
                pause_stop = task.start_time

                # Computing work time
                tw = task.work_time
                work_str = '%s' % ':'.join(str(task.work_time).split(':')[0:2])
                start_str = '%s' % task.start_time.strftime('%H:%M')
                end_str = '%s' % task.end_time.strftime('%H:%M')

                column += '%s | %s -> %s = %s | %s' % (task.end_date, start_str, end_str, work_str, task.name)
                column += '\n'

            print('-' * 60)
            print(column)
            print('Work: {wtime},  Break: {btime}'.format(wtime=tot_time, btime=pause))
            print('')

        return tot_time, pause

def do_report(args):
    filter = args['<filter>']
    if not filter and not args['--all']:
        filter = datetime.datetime.strftime(datetime.datetime.today(), '%Y-%m-%d')
    if args['--yesterday']:
        yesterday = datetime.datetime.today() - datetime.timedelta(1)
        filter = str(yesterday).split()[0]
    if args['--full']:
        report_full(filter)
    elif args['--daily']:
        map = group_task_by(get_tasks(lambda x: not filter or filter in str(x.end_date)),
                            'date')
        for key in sorted(map.keys()):
            t = group_task_by(map[key], 'task')
            report_task(t)
    else:
        tasks = group_task_by(get_tasks(lambda x: not filter or (filter in str(x.end_date) or filter in x.name)),
                              'task')
        report_task(tasks)
    return


def main():
    args = docopt.docopt(__doc__)

    if args['<name>']:
        if args['--change']:
            new_task_name = ' '.join(args['<name>'])
            Task.change(new_task_name)
            return
        elif not Task.get_running():
            new_task_name = ' '.join(args['<name>'])
            Task(new_task_name).start()
        else:
            pass
    else:
        if args['--stop']:
            Task.stop(args['--time'])

        elif args['--replace']:
            target = ' '.join(args['--replace'])
            replacement = ' '.join(args['--with'])
            dbg ("replacing '{0}' with '{1}'".format(target, replacement))
            Task.change(replacement, target)

        elif args['--to']:
            Task.stop()
            new_task_name = ' '.join(args['<newtask>'])
            Task(new_task_name).start()

        elif args['--keep']:
            id = eval(args['--keep'])
            keep(start_time_str=args['--time'], id=id)

        elif args['--report']:
            do_report(args)

        elif args['--autocomplete']:
            autocomplete()

        elif Task.get_running():
            Task.status()

        elif not args['<name>']:
            args['<name>'] = ['unknown']

            return do_report(args)


if __name__ == '__main__':
    main()
