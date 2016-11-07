#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Usage:
    letsdo [--force] [<name>]
    letsdo --change <newname>
    letsdo --report [<filter>]
    letsdo --stop
    letsdo --to    <newtask>

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

# Configuration
DATA_FILENAME = os.path.expanduser(os.path.join('~', '.letsdo-data'))
TASK_FILENAME = os.path.expanduser(os.path.join('~', '.letsdo-task'))
args = docopt.docopt(__doc__)

# Logger
level = logging.INFO
logging.basicConfig(level=level, format='  %(message)s')
logger = logging.getLogger(__name__)
info = lambda x: logger.info(x)
err = lambda x: logger.error(x)
warn = lambda x: logger.warn(x)
dbg = lambda x: logger.debug(x)

dbg(args)


class Task(object):
    def __init__(self, name='unknown', start=None, end=None):
        self.name = name
        if start:
            self.start_time = start
        else:
            self.start_time = datetime.datetime.now()

    @staticmethod
    def get():
        if Task.__is_running():
            with open(TASK_FILENAME, 'r') as f:
                return pickle.load(f)

    @staticmethod
    def stop():
        task = Task.get()
        if task:
            os.remove(TASK_FILENAME)

            work, now = task.__elapsed_time()
            status = ('Stopped task \'%s\' after %s of work' % (task.name, work)).split('.')[0]
            info(status)

            date = datetime.date.today()
            report = '%s,%s,%s,%s,%s\n' % (date, task.name, work, task.start_time, now)
            with open(DATA_FILENAME, mode='a') as f:
                f.writelines(report)
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
        with open(TASK_FILENAME, 'w') as f:
            pickle.dump(self, f)
            return True

    def __elapsed_time(self):
        now = datetime.datetime.now()
        return now - self.start_time, now

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
                start = entry[3].split('.')[0].strip()
                stop = entry[4].split('.')[0].strip()

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
    if args['--stop']:
        Task.stop()
    elif args['--change']:
        Task.change(args['<newname>'])
    elif args['--to']:
        Task.stop()
        Task(args['<newtask>']).start()
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

        args['<name>'] = 'unknown'
        Task(args['<name>']).start()


if __name__ == '__main__':
    main()
