#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Usage:
    gtd start  [--debug] [<name>]
    gtd stop   [--debug]
    gtd status [--debug]
    gtd report
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
rbg = lambda x: logger.debug(x)


def get_data():
    if os.path.exists(TASK_FILENAME):
        with open(TASK_FILENAME, 'r') as f:
            return pickle.load(f)


if __name__ == '__main__':
    now = datetime.datetime.now()
    DATA_FILENAME = '/home/carlolo/.gtd-data'
    TASK_FILENAME = '/home/carlolo/.gtd-task'

    if args['start']:
        if os.path.exists(TASK_FILENAME):
            warn('Another task is running!')
        else:
            data = {'time': now, 'name': args['<name>']}
            with open(TASK_FILENAME, 'w') as f:
                pickle.dump(data, f)

    if args['status'] or args['stop']:
        d = get_data()

        if d:
            work = now - d['time']
            if args['stop']:
                os.remove(TASK_FILENAME)
                status = ('Stopped task \'%s\' after %s of work' % (d['name'], work)).split('.')[0]

                date = datetime.date.today()
                report = '%s,%s,%s' % (date, d['name'], work)
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
                wtime = datetime.datetime.strptime(wtime_str, '%H:%M:%S')

                if date not in report.keys():
                    report[date] = {name: wtime}
                else:
                    if name not in report[date].keys():
                        report[date][name] = wtime
                    else:
                        cur = report[date][name]
                        newtime = datetime.datetime(
                                year=wtime.year,
                                month=wtime.month,
                                day=wtime.day,
                                hour=wtime.hour+cur.hour,
                                minute=wtime.minute+cur.minute,
                                second=wtime.second+cur.second)
                        report[date][name] = newtime
        dates = sorted(report.keys())
        for date in dates:
            entry = report[date]
            for name, wtime in entry.items():
                print('%s| %s: %s' % (date, name, datetime.datetime.strftime(wtime, '%H:%M')))



