#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Usage:
    letsdo [--time=<time>] [--work-on=<id>|<name>...]
    letsdo --list
    letsdo --change <name>...
    letsdo --replace=<target>... --with=<string>...
    letsdo --to [<newtask>...|--id=<id>]
    letsdo --stop [--time=<time>]
    letsdo --report [--by-name|--detailed]
    letsdo --report --yesterday [--by-name|--detailed]
    letsdo --report --all [--by-name|--detailed] [<pattern>]
    letsdo --report --daily [--all] [--yesterday] [<pattern>]
    letsdo --autocomplete

options:
    --debug                     Enable debug logs
    --id<id>                    Task id (used with --to)
    --to                        Stop current task and switch to a new one
    -a --all                    Report activities for all stored days
    -c --change                 Rename current task
    -d --daily                  Report today activities by task
    -f --full                   Report today full activity with start/end time
    -l, --list                  Show Todo list
    -r --report                 Report whole time spent on each task
    -s --stop                   Stop current running task
    -t <time> --time=<time>     Suggest the start/stop time of the task
    -w <id>, --work-on=<id>     Start working on a Task giving it's ID
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
                self.data_dir = os.path.expanduser(configuration['DATADIR'])
                self.data_fullpath = os.path.join(self.data_dir, '.letsdo-data')
            except KeyError as e:
                err('Config file error: Could not find \'{msg}\' field'.format(msg=e.message))
                info('letsdo data will be saved into HOME directory')
                self.data_fullpath = os.path.expanduser(os.path.join('~', '.letsdo-data'))
            dbg('Configuration: data filename {file}'.format(file = self.data_fullpath))

            try:
                self.task_fullpath = os.path.join(self.data_dir, '.letsdo-task')
            except KeyError as e:
                err('Config file error: Could not find \'{msg}\' field'.format(msg=e.message))
                info('letsdo data will be saved into HOME directory')
                self.task_fullpath = os.path.expanduser(os.path.join('~', '.letsdo-data'))
            dbg('Configuration: task filename {file}'.format(file = self.task_fullpath))

            try:
                self.todo_fullpath = os.path.expanduser(configuration['TODO_FULLPATH'])
            except KeyError as e:
                dbg('Config file: Could not find \'{msg}\' field'.format(msg=e.message))

            try:
                self.todo_start_tag = os.path.expanduser(configuration['TODO_START_TAG'])
            except KeyError as e:
                dbg('Config file: Could not find \'{msg}\' field'.format(msg=e.message))
                self.todo_start_tag = None

            try:
                self.todo_stop_tag = os.path.expanduser(configuration['TODO_STOP_TAG'])
            except KeyError as e:
                dbg('Config file: Could not find \'{msg}\' field'.format(msg=e.message))
                self.todo_stop_tag = None

        else:
            dbg('Config file not found. Using default')
            self.data_fullpath = os.path.expanduser(os.path.join('~', '.letsdo-data'))
            self.task_fullpath = os.path.expanduser(os.path.join('~', '.letsdo-task'))



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
        TASK_FILENAME = Configuration().task_fullpath
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
        DATA_FILENAME = Configuration().data_fullpath
        with open(DATA_FILENAME, mode='a') as f:
            f.writelines(report)

        TASK_FILENAME = Configuration().task_fullpath
        os.remove(TASK_FILENAME)
        hours, minutes = work_time_str.split(':')
        info('Stopped \'{name}\' for {h}h {m}m'.format(
                    name=task.name, h=hours, m=minutes))
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
            time = str(now - task.start_time).split('.')[0]
            hours, minutes, seconds = time.split(':')
            info('Working on \'{name}\' for {h}h {m}m {s}s'.format(
                    name=task.name, h=hours, m=minutes, s=seconds))
            return True
        else:
            info('No task running')
            return False

    @staticmethod
    def __is_running():
        TASK_FILENAME = Configuration().task_fullpath
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
        TASK_FILENAME = Configuration().task_fullpath
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
        if self.start_time:
            start_str = '%s' % self.start_time.strftime('%H:%M')
        else:
            start_str = 'None'

        if self.end_time:
            end_str = '%s' % self.end_time.strftime('%H:%M')
        else:
            end_str = 'None'

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
    print('--- CUT HERE ------------------------------------------------------------------')
    message = '''
    Do you want me to configure this automatically, copying the above script in your
    $HOME directory? [Y/n]
    '''
    info(message)

    resp = raw_input()
    if resp.lower() == 'y':
        completionfile = os.path.join(os.path.expanduser('~',), '.letsdo_completion')
        with open(completionfile, 'w') as f:
            f.writelines(open(completion).read())


def format_h_m(string):
    h, m = string.split(':')[0:2]
    return '{0}h {1}m'.format(h, m)
    #return ':'.join(string.split(':')[0:2])

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


def work_on(task_id=0, start_time_str=None):
    tasks = get_tasks(condition=lambda x: x.id == task_id)
    tasks = group_task_by(tasks, group='name')
    if not tasks:
        err ("Could not find any task with ID '{id}'".format(id=task_id))
    else:
        assert (len(tasks) == 1)
        task = tasks[0]
        start_time = None
        if start_time_str:
            date_str = datetime.datetime.strftime(datetime.datetime.today(), '%Y-%m-%d')
            start_time = date_str + ' ' + start_time_str

        Task(task.name, start=start_time).start()


def sanitize(text, filters=[]):
    # remove initial list symbol (if any)
    if re.match('[\-\*]', text):
        text = re.sub('^[\-\*]', '', text)

    # remove initial date (yyyy-mm-dd)
    if re.match('^\s*\d+-\d+-\d+\s+', text):
        text = re.sub('^\s*\d+-\d+-\d+\s+', '', text)

    # remove initial date (yy\date-of-year)
    if re.match('^\s*\d+/\d+\s+', text):
        text = re.sub('^\s*\d+/\d+\s+', '', text)

    # remove markdown links
    md_link = re.compile('\[(.*)\]\(.*\)')
    has_link = md_link.search(text)
    if has_link:
        link_name = md_link.findall(text)
        assert(len(link_name) == 1)
        text = re.sub('\[(.*)\]\(.*\)', link_name[0], text)

    return text


def get_todos():
    tasks = []
    try:
        with open(Configuration().todo_fullpath, 'r') as f:
            todo_start_tag = Configuration().todo_start_tag
            todo_stop_tag = Configuration().todo_stop_tag

            if todo_start_tag:
                read = False
                id = 0
                for line in f.readlines():
                    if todo_start_tag in line.lower():
                        read = True
                        continue
                    if (todo_stop_tag and todo_stop_tag in line.lower()) or not line.strip():
                        read = False
                        break

                    if read:
                        line = sanitize(line)
                        id += 1
                        tasks.append(Task(name=line, id=id))
            else:
                tasks = [Task(name=sanitize(line), id=lineno+1) for lineno, line in enumerate(f.readlines())]
    except (AttributeError, IOError):
        dbg ("Could not find todo file '{filepath}'".format(filepath=Configuration().todo_fullpath))
    return tasks


def get_tasks(condition=None, todos=None):
    datafilename = Configuration().data_fullpath
    # Some todos might have been logged yet and some other don't.
    # Pass this list to avoid duplication, but I do not like
    # this solution
    if todos:
        tasks = todos
    else:
        tasks = get_todos()
    id = len(tasks)
    try:
        with open(datafilename) as f:
            for line in reversed(f.readlines()):
                dbg(line)
                fields = line.strip().split(',')
                t = Task(name=fields[1],
                         start=fields[3],
                         end=fields[4])
                # If a task with the same name exists,
                # keep the same ID as well
                try:
                    same_task = tasks.index(t)
                    t.id = tasks[same_task].id
                    dbg('{task_name} has old id {id}'.format(task_name=t.name, id=t.id))
                except ValueError:
                    id += 1
                    t.id = id
                    dbg('{task_name} has new id {id}'.format(task_name=t.name, id=t.id))
                tasks.append(t)

        return filter(condition, tasks)
    except IOError:
        return []


def group_task_by(tasks, group=None):
    groups = []
    if group is 'name':
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
    info('----------------------------------------')
    for task in tasks:
        tot_work_time += task.work_time
        info('#{id:03d} ~ {worked:8s}--- {name}'.format(id=task.id,
            worked=format_h_m(str(task.work_time)),
            name=task.name))
    info('----------------------------------------')
    if filter:
        info('{filter}: Total work time {time}'.format(filter=filter, time=format_h_m(str(tot_work_time))))
    else:
        info('Total work time {time}'.format(filter=filter, time=format_h_m(str(tot_work_time))))
    info('')


def report_full(filter=None):
    tasks = {}
    datafilename = Configuration().data_fullpath
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
    pattern = args['<pattern>']
    if not args['--all']:
        if not args['--yesterday']:
            # By default show --today's tasks
            today_date = datetime.datetime.strftime(datetime.datetime.today(), '%Y-%m-%d')
            by_logged_today = lambda x: today_date in str(x.end_date)
            tasks = get_tasks(by_logged_today)
        else:
            yesterday = datetime.datetime.today() - datetime.timedelta(1)
            yesterday_date = str(yesterday).split()[0]   # keep only the part with YYYY-MM-DD
            by_logged_yesterday = lambda x: yesterday_date in str(x.end_date)
            tasks = get_tasks(by_logged_yesterday)

    else:
        by_name_or_end_date = lambda x: not pattern or (pattern in str(x.end_date) or pattern in x.name)
        tasks = get_tasks(by_name_or_end_date)

    # By default show Task grouped by name
    if not args['--detailed']:
        tasks = group_task_by(tasks, 'name')
        report_task(tasks)
    else:
        pass

    #if args['--full']:
    #    report_full(filter)
    #elif args['--daily']:
    #    by_end_date = lambda x: not filter or filter in str(x.end_date)
    #    map = group_task_by(get_tasks(by_end_date), 'date')

    #    for key in sorted(map.keys()):
    #        t = group_task_by(map[key], 'task')
    #        report_task(t)
    #else:
    #    tasks = group_task_by(get_tasks(by_name_or_end_date), 'task')
    #    report_task(tasks)


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
        if args['--list']:
            todos = get_todos()
            names = [t.name for t in todos]

            in_todo_list = lambda x: x.name in names
            tasks = get_tasks(in_todo_list, todos)
            tasks = group_task_by(tasks, 'name')
            report_task(tasks)

        elif args['--stop']:
            Task.stop(args['--time'])

        elif args['--replace']:
            target = ' '.join(args['--replace'])
            replacement = ' '.join(args['--with'])
            dbg ("replacing '{0}' with '{1}'".format(target, replacement))
            Task.change(replacement, target)

        elif args['--to']:
            if args['--id']:
                id = eval(args['--id'])
                tasks = get_tasks(lambda x: x.id == id)
                if len(tasks) == 0:
                    err ("Could not find tasks with id '%d'" & id)
                else:
                    task = tasks[0]
                    new_task_name = task.name
            else:
                new_task_name = ' '.join(args['<newtask>'])

            Task.stop()
            Task(new_task_name).start()

        elif args['--work-on']:
            id = eval(args['--work-on'])
            work_on(task_id=id, start_time_str=args['--time'])
            sys.exit(0)

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
