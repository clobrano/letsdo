#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Usage:
    letsdo start  [--debug] <task> [--rename=name]
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

def get_data():
    if os.path.exists(TASK_FILENAME):
        with open(TASK_FILENAME, 'r') as f:
            return pickle.load(f)
    warn('No task is running')


def save_data(data):
   with open(TASK_FILENAME, 'w') as f:
        pickle.dump(data, f)


def start(name):
    if os.path.exists(TASK_FILENAME):
        warn('Another task is running!')
    else:
        now = datetime.datetime.now()
        save_data({'time': now, 'name': name})
        info('Starting task \'%s\' now' % name)


def stop():
    task = get_data()
    if task:
        os.remove(TASK_FILENAME)

        now = datetime.datetime.now()
        work = now - task['time']
        status = ('Stopped task \'%s\' after %s of work' % (task['name'], work)).split('.')[0]
        info(status)

        date = datetime.date.today()
        report = '%s,%s,%s\n' % (date, task['name'], work)
        with open(DATA_FILENAME, mode='a') as f:
            f.writelines(report)

if __name__ == '__main__':
    now = datetime.datetime.now()
    DATA_FILENAME = '/home/carlolo/.gtd-data'
    TASK_FILENAME = '/home/carlolo/.gtd-task'

    if args['start']:
        if args['<task>'] is None:
            args['<task>'] = 'unknown'
        elif os.path.exists(TASK_FILENAME):
            warn('Another task is running!')
        else:
            save_data({'time': now, 'name': args['<task>']})

    if args['rename']:
        data = get_data()
        if data:
            data['name'] = args['<newname>']
            save_data(data)

    if args['to']:
        stop()
        start(args['<task>'])

    if args['status'] or args['stop']:
        d = get_data()

        if d:
            work = now - d['time']
            if args['stop']:
                os.remove(TASK_FILENAME)
                status = ('Stopped task \'%s\' after %s of work' % (d['name'], work)).split('.')[0]

                date = datetime.date.today()
                report = '%s,%s,%s\n' % (date, d['name'], work)
                with open(DATA_FILENAME, mode='a') as f:
                    f.writelines(report)
            else:
                status = ('Working on \'%s\' for %s' % (d['name'], work)).split('.')[0]
            info(status)
        else:
            info('No running tasks')

    if args['report']:
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
                column += ('%s| %s\n' % (date, (str(wtime) + ' - ' + name)))
            print('===================================')
            print('%s| Total time: %s' % (date, tot_time))
            print('-----------------------------------')
            print(column)

