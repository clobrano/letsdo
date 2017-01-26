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
    letsdo --report [--all] [--yesterday] [<filter>]
    letsdo --report --full [--all] [--yesterday] [<filter>]
    letsdo --report --daily [--all] [--yesterday] [<filter>]
    letsdo --autocomplete

Notes:
    With no arguments, letsdo start a new task or report the status of the current running task

    -a --all                    Report activities for all stored days
    --to                        Stop current task and switch to a new one
    -c --change                 Rename current task
    -d --daily                  Report today activities by task
    -f --full                   Report today full activity with start/end time
    -i <id> --id=<id>           Task id
    -k --keep                   Restart last run task
    -r --report                 Report whole time spent on each task
    -s --stop                   Stop current running task
    -t <time> --time=<time>     Suggest the start/stop time of the task
    -y --yesterday              Fast switch to show reports of the day before
'''

import os
import datetime
import time
import docopt
import sys
import logging
import yaml
import re

from persistance import Configuration
from tasks import Task
from reports import do_report

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


def main():
    args = docopt.docopt(__doc__)

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
        return do_report(args)

    if args['--autocomplete']:
        autocomplete()
        return

    if Task.get():
        Task.status()
        return

    if not args['<name>']:
        args['<name>'] = ['unknown']

        if not args['--force']:
            return do_report(args)

    new_task_name = ' '.join(args['<name>'])
    Task(new_task_name, start=args['--time']).start()


if __name__ == '__main__':
    main()
