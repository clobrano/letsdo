#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Usage:
    letsdo [--force] [<name>...]
    letsdo --change <newname>...
    letsdo --report [<filter>]
    letsdo --stop   [<time>]
    letsdo --to    <newtask>...

Notes:
    With no arguments, letsdo start a new task or report the status of the current running task
    -s --stop          Stop current running task
    -c --change        Rename current running task
    -t --to            Switch task
    -f --force         Start new unnamed task without asking
    -r --report        Get the full report of task done (with a filter on date if provided)
'''

import os
import pickle
import datetime
import time
import docopt
import sys
import logging
import yaml

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
            self.data_filename = os.path.expanduser(os.path.join(configuration['DATAFILE'], '.letsdo-data'))
            self.task_filename = os.path.expanduser(os.path.join(configuration['TASKFILE'], '.letsdo-task'))
        else:
            dbg('Config file not found. Using default')
            self.data_filename = os.path.expanduser(os.path.join('~', '.letsdo-data'))
            self.task_filename = os.path.expanduser(os.path.join('~', '.letsdo-task'))



class Task(object):
    def __init__(self, name='unknown', start=None, end=None):
        self.name = name
        if start:
            self.start_time = start
        else:
            self.start_time = datetime.datetime.now()

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
                stop_time_date = datetime.datetime.strftime(stop_time, '%Y-%m-%d')
                stop_time = datetime.datetime.strptime(stop_time_date + ' ' + stop_time_str, '%Y-%m-%d %H:%M')

                if stop_time < task.start_time:
                    warn('Given stop time (%s) is more recent than start time (%s)' % (stop_time, task.start_time))
                    return False

            work = stop_time - task.start_time
            status = ('Stopped task \'%s\' after %s of work' % (task.name, work)).split('.')[0]
            info(status)

            date = datetime.date.today()
            report = '%s,%s,%s,%s,%s\n' % (date, task.name, work, task.start_time, stop_time)
            DATA_FILENAME = Configuration().data_filename
            with open(DATA_FILENAME, mode='a') as f:
                f.writelines(report)

            TASK_FILENAME = Configuration().task_filename
            os.remove(TASK_FILENAME)
            return True
        info('No task running')
        return False

    @staticmethod
    def change(name):
        task = Task.get()
        if task:
            info('Renaming task \'%s\' to \'%s\'' % (task.name, name))
            task.name = name
            return task.__create()

        warn('No task running')

    @staticmethod
    def status():
        task = Task.get()
        if task:
            now = datetime.datetime.now()
            work = now - task.start_time
            status = ('Working on \'%s\' for %s' % (task.name, work)).split('.')[0]
            info(status)
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
                info('Starting task \'%s\' now' % self.name)
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


def report(filter=None):
    report = {}
    with open(DATA_FILENAME) as f:
        for line in f.readlines():
            entry = line.split(',')

            date = entry[0]
            if filter and filter not in date:
                continue

            name = entry[1]
            wtime_str = entry[2].split('.')[0].strip()
            wtime_date = datetime.datetime.strptime(wtime_str, '%H:%M:%S')
            wtime = datetime.timedelta(
                    hours=wtime_date.hour,
                    minutes=wtime_date.minute,
                    seconds=wtime_date.second)
            # To be kept for retrocompatibility
            if len(entry) > 3:
                start_time = entry[3].split('.')[0].strip()
                stop_time = entry[4].split('.')[0].strip()

            if date not in report.keys():
                report[date] = {name: wtime}
            else:
                if name not in report[date].keys():
                    report[date][name] = wtime
                else:
                    report[date][name] += wtime

    dates = sorted(report.keys(), reverse=True)
    for date in dates:
        entry = report[date]
        tot_time = datetime.timedelta()
        column = ''
        for name, wtime in entry.items():
            tot_time += wtime
            column += ('%s| %s - %s\n' % (date, wtime,  name))
        print('===================================')
        print('%s| Total time: %s' % (date, tot_time))
        print('-----------------------------------')
        print(column)



def main():
    # Configuration
    args = docopt.docopt(__doc__)
    dbg(args)

    global DATA_FILENAME
    global TASK_FILENAME
    conf = Configuration()
    DATA_FILENAME = conf.data_filename
    TASK_FILENAME = conf.task_filename

    if args['--stop']:
        Task.stop(args['<time>'])
    elif args['--change']:
        new_task_name = ' '.join(args['<newname>'])
        Task.change(new_task_name)
    elif args['--to']:
        Task.stop()
        new_task_name = ' '.join(args['<newtask>'])
        Task(new_task_name).start()
    elif args['--report']:
        report(args['<filter>'])
    else:
        if Task.get():
            Task.status()
            sys.exit(0)
        elif not args['<name>'] and not args['--force']: # Not sure if asking for status or starting an unnamed task
            resp = raw_input('No running task. Let\'s create a new unnamed one [y/n]?: ')
            if resp.lower() != 'y':
                sys.exit(0)
            args['<name>'] = ['unknown']

        new_task_name = ' '.join(args['<name>'])
        Task(new_task_name).start()


if __name__ == '__main__':
    main()
