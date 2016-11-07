#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Usage:
    letsdo start  [--debug] [<task>]
    letsdo rename [--debug] <newname>
    letsdo stop   [--debug]
    letsdo status [--debug]
    letsdo report [--debug]
    letsdo to     [--debug] <task>

Notes:
    letsdo to     Stop the current task and start a new one.
'''

import os
import pickle
import datetime
import time
import docopt
import sys
import logging

# Configuration
DATA_FILENAME = '/home/carlolo/.letsdo-data'
TASK_FILENAME = '/home/carlolo/.letsdo-task'
args = docopt.docopt(__doc__)

# Logger
if args['--debug']:
    level = logging.DEBUG
else:
    level = logging.INFO
logging.basicConfig(level=level, format='  %(message)s')
logger = logging.getLogger(__name__)
info = lambda x: logger.info(x)
err = lambda x: logger.error(x)
warn = lambda x: logger.warn(x)
dbg = lambda x: logger.debug(x)

dbg(args)


class Task(object):
    def __init__(self, name, start=None, end=None):
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
        else:
            info('No task running')

    @staticmethod
    def rename(name):
        task = Task.get()
        if task:
            info('Renaming task \'%s\' to \'%s\'' % (task.name, name))
            task.name = name
            task.__create()
        else:
            warn('No task running')

    @staticmethod
    def status():
        task = Task.get()
        if task:
            now = datetime.datetime.now()
            work = now - task.start_time
            status = ('Working on \'%s\' for %s' % (task.name, work)).split('.')[0]
            info(status)
        else:
            info('No task running')

    @staticmethod
    def __is_running():
        exists = os.path.exists(TASK_FILENAME)
        dbg('is it running? %d' % exists)
        return exists

    def start(self):
        if not Task.__is_running():
            self.__create()
            info('Starting task \'%s\' now' % self.name)
        else:
            warn('Another task is running')

    def __create(self):
        with open(TASK_FILENAME, 'w') as f:
            pickle.dump(self, f)

    def __elapsed_time(self):
        now = datetime.datetime.now()
        return now - self.start_time, now

def report():
    report = {}
    with open(DATA_FILENAME) as f:
        for line in f.readlines():
            entry = line.split(',')
            date = entry[0]
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
    if args['start']:
        if args['<task>'] is None:
            args['<task>'] = 'unknown'
        Task(args['<task>']).start()

    if args['rename']:
        Task.rename(args['<newname>'])

    if args['to']:
        Task.stop()
        Task(args['<task>']).start()

    if args['stop']:
        Task.stop()

    if args['status']:
        Task.status()

    if args['report']:
        report()


if __name__ == '__main__':
    main()
