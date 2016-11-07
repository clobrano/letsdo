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
    def __init__(self, name, start=datetime.datetime.now(), end=None):
        self.end = end
        self.name = name
        self.start = start

    @staticmethod
    def get():
        if os.path.exists(TASK_FILENAME):
            with open(TASK_FILENAME, 'r') as f:
                return pickle.load(f)

    def start(self):
        self.save()
        info('Starting task \'%s\' now' % self.name)

    def save(self):
        with open(TASK_FILENAME, 'w') as f:
            pickle.dump(self, f)


def get_data():
    if os.path.exists(TASK_FILENAME):
        with open(TASK_FILENAME, 'r') as f:
            return pickle.load(f)
    warn('No task is running')


def save_data(data):
   with open(TASK_FILENAME, 'w') as f:
        pickle.dump(data, f)


def start(name):
    task = Task.get()
    if task:
        warn('Another task is running!')
    else:
        Task(name).save()


def stop():
    task = Task.get()
    if task:
        os.remove(TASK_FILENAME)

        now = datetime.datetime.now()
        work = now - task.start
        status = ('Stopped task \'%s\' after %s of work' % (task.name, work)).split('.')[0]
        info(status)

        date = datetime.date.today()
        report = '%s,%s,%s,%s,%s\n' % (date, task.name, work, task.start, now)
        with open(DATA_FILENAME, mode='a') as f:
            f.writelines(report)


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


def status():
    task = Task.get()
    if task:
        now = datetime.datetime.now()
        work = now - task.start
        status = ('Working on \'%s\' for %s' % (task.name, work)).split('.')[0]
        info(status)

def rename(name):
    task = Task.get()
    if task:
        info('Renaming task \'%s\' to \'%s\'' % (task.name, name))
        task.name = name
        task.save()

def main():
    if args['start']:
        if args['<task>'] is None:
            args['<task>'] = 'unknown'
        start(args['<task>'])

    if args['rename']:
        rename(args['<newname>'])

    if args['to']:
        stop()
        start(args['<task>'])

    if args['stop']:
        stop()

    if args['status']:
        status()

    if args['report']:
        report()


if __name__ == '__main__':
    main()
