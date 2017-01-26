#!/usr/bin/env python
# -*- coding: utf-8 -*-
import datetime
import logging
from configuration import Configuration
from tasks import Task

# Logger
level = logging.INFO
logging.basicConfig(level=level, format='  %(message)s')
logger = logging.getLogger(__name__)
info = lambda x: logger.info(x)
err = lambda x: logger.error(x)
warn = lambda x: logger.warn(x)
dbg = lambda x: logger.debug(x)

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


def get_tasks(condition=None):
    tasks = []
    datafilename = Configuration().data_filename
    id = -1
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
    info('========================================')
    info('#ID    Worked (Last  Time)| task name')
    info('----------------------------------------')
    for task in tasks:
        if not filter or (filter in str(task.start_time) or filter in task.name):
            tot_work_time += task.work_time
            info('#{id:03d} {worked:>8s} ({lasttime})| {name}'.format(id=task.id,
                worked=task.work_time,
                name=task.name,
                lasttime=task.end_date))
    info('----------------------------------------')
    info('Total work time %s' % tot_work_time)
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
                tot_time += task.work_time
                work_str = '%s' % str(task.work_time).split('.')[0]
                start_str = '%s' % task.start_time.strftime('%H:%M')
                end_str = '%s' % task.end_time.strftime('%H:%M')

                column += '%s| %s (%s -> %s) - %s' % (task.end_date, work_str, start_str, end_str, task.name)
                column += '\n'

            print('===========================================')
            print('%s| Work: %s | Break: %s') % (date, tot_time, pause)
            print('-------------------------------------------')
            print(column)

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


