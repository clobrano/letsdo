#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
Usage:
    lets see    [todo|all|today|yesterday|config] [--detailed|--day-by-day] [--ascii] [<pattern>] [--no-color]
    lets do     [--time=<time>] [<name>...] [--no-color]
    lets stop   [--time=<time>] [--no-color]
    lets goto   [<newtask>...] [--no-color]
    lets cancel [--no-color]
    lets edit
    lets config data.directory <fullpath>
    lets config todo.file      <fullpath>
    lets config todo.start_tag <tag>
    lets config todo.stop_tag  <tag>
    lets config autocomplete

options:
    -a, --ascii       Print report table in ASCII characters
    -t, --time=<time> Change the start/stop time of the task on the fly
    -n, --no-color    Disable colorizer (depends on raffaello python package)
'''

import os
import hashlib
import re
import json
from datetime import datetime, timedelta
import docopt
from terminaltables import SingleTable, AsciiTable
from log import info, LOGGER, RAFFAELLO
from configuration import Configuration, autocomplete
from timetoolkit import str2datetime, strfdelta

CONFIGURATION = Configuration()


def paint(msg):
    '''Returns a colorized copy of the input message'''
    if msg and RAFFAELLO:
        return RAFFAELLO.paint(str(msg))

    return msg


class Task(object):
    '''A running task object'''
    def __init__(self, name, start_str=None, end_str=None, tid=None):
        self.context = None
        self.tags = None
        self.__parse_name(name.strip())
        self.uid = self.__hash()
        self.tid = tid

        # Adjust Task's start time with a string representing a
        # time or a date + time,
        # otherwise the task starts now.
        # See std2datetime for available formats.
        if start_str:
            self.start_time = str2datetime(start_str.strip())
        else:
            self.start_time = datetime.now()

        if end_str:
            self.end_time = str2datetime(end_str.strip())
            self.work_time = self.end_time - self.start_time
        else:
            self.end_time = None
            self.work_time = timedelta()

    @property
    def last_end_date(self):
        ''' The last day when this Task was active'''
        if self.end_time:
            return self.end_time.strftime('%Y-%m-%d')
        return None

    @staticmethod
    def __is_running():
        exists = os.path.exists(CONFIGURATION.task_fullpath)
        LOGGER.debug('Is a task running? {}'.format(exists))
        return exists

    @staticmethod
    def get_running():
        '''Check whether a task is running'''
        if Task.__is_running():
            with open(CONFIGURATION.task_fullpath, 'r') as cfile:
                data = json.load(cfile)
                return Task(data['name'], data['start'])
        return None

    @staticmethod
    def stop(stop_time_str=None):
        '''Stop task'''
        task = Task.get_running()
        if not task:
            info('No task running')
            return

        # Get strings for the task report
        if stop_time_str:
            stop_time = str2datetime(stop_time_str)
            if stop_time < task.start_time:
                LOGGER.warn('Given stop time (%s) is more recent than start time (%s)'
                            % (stop_time, task.start_time))
                return False
            date = stop_time.strftime('%Y-%m-%d')
        else:
            stop_time = datetime.now()
            date = datetime.today()

        work_time_str = str(stop_time - task.start_time).split('.')[0][:-3]
        start_time_str = str(task.start_time).split('.')[0][:-3]
        stop_time_str = str(stop_time).split('.')[0][:-3]

        report_line = '{date},{name},{start_time},{stop_time}\n'\
                      .format(date=date,
                              name=task.name,
                              start_time=start_time_str,
                              stop_time=stop_time_str)

        try:
            with open(CONFIGURATION.data_fullpath, mode='a') as cfile:
                cfile.writelines(report_line)
        except IOError as error:
            LOGGER.error('Could not save report: ' + error.message)
            return False

        # Delete current task data to mark it as stopped
        os.remove(CONFIGURATION.task_fullpath)

        hours, minutes = work_time_str.split(':')
        info('Stopped \'{name}\' after {h}h {m}m of work'.format(
            name=task.name, h=hours, m=minutes))

        return True

    @staticmethod
    def cancel():
        '''Interrupt task without saving it in history'''
        task = Task.get_running()
        if task:
            with open(CONFIGURATION.task_fullpath, 'r') as cfile:
                content = cfile.read()
            os.remove(CONFIGURATION.task_fullpath)
            info('Cancelled task')
            info(content)

    @staticmethod
    def status():
        '''Get status of current running task'''
        task = Task.get_running()
        if task:
            now = datetime.now()
            time = str(now - task.start_time).split('.')[0]
            hours, minutes, seconds = time.split(':')
            info('Working on \'{name}\' for {h}h {m}m {s}s'
                 .format(name=task.name,
                         h=hours,
                         m=minutes,
                         s=seconds))
            return True
        info('No task running')
        return False

    def start(self):
        '''Start task'''
        if not Task.__is_running():
            if self.__create():
                return Task.get_running()

            LOGGER.error('Could not create new task')
            return False

        LOGGER.warn('Another task is running')
        return True

    def __hash(self):
        gen = hashlib.sha256(self.name.encode())
        return gen.hexdigest()

    def __create(self):
        try:
            with open(CONFIGURATION.task_fullpath, 'w') as cfile:
                json_data = '''{
    "name": %s,
    "start": %s
}
''' % (json.dumps(self.name), json.dumps(str(self.start_time)))
                cfile.write(json_data)
                info('Started task:')
                info(json_data)
                return True
        except IOError as error:
            LOGGER.error('Could not save task data: ' + error.message)
            return False

    def __parse_name(self, name):
        # Sanitizing name (commas are still used to separate infos and cannot
        # be used in task's name
        name = name.replace(',', ' ')
        self.name = name
        # Storing contexts (@) and projects (+)
        matches = re.findall(r'@[\w\-_]+', name)
        if len(matches) == 1:
            self.context = matches[0]
        matches = re.findall(r'\+[\w\-_]+', name)
        if len(matches) >= 1:
            self.tags = matches

    def __repr__(self):
        if self.start_time:
            start_str = '%s' % self.start_time.strftime('%H:%M')
        else:
            start_str = 'None'

        if self.end_time:
            end_str = '%s' % self.end_time.strftime('%H:%M')
            work_str = '%s' % str(self.work_time).split('.')[0]
        else:
            end_str = 'None'
            work_str = 'in progress'

        if self.tid is not None:
            return '[%d:%s] - %s| %s (%s -> %s) - %s' % (self.tid,
                                                         self.uid,
                                                         self.last_end_date,
                                                         work_str,
                                                         start_str,
                                                         end_str,
                                                         self.name)

        return '[%s] - %s| %s (%s -> %s) - %s' % (self.uid,
                                                  self.last_end_date,
                                                  work_str,
                                                  start_str,
                                                  end_str,
                                                  self.name)

    def __eq__(self, other):
        return self.name == other.name

    def __ne__(self, other):
        return self.name != other.name


def work_on(task_id=0, start_time_str=None):
    '''Start given task id'''
    tasks = get_tasks(condition=lambda x: x.tid == task_id)
    tasks = group_task_by(tasks, group='name')
    if not tasks:
        LOGGER.error("Could not find any task with ID '{id}'".format(id=task_id))
    else:
        assert(len(tasks) == 1)
        task = tasks[0]
        start_time = None
        if start_time_str:
            date_str = datetime.strftime(datetime.today(),
                                         '%Y-%m-%d')
            start_time = date_str + ' ' + start_time_str

        Task(task.name, start_str=start_time).start()


def sanitize(text):
    '''Remove symbols, dates and Markdown syntax from text'''
    # remove initial list symbol (if any)
    if re.match(r'^[\-\*]', text):
        text = re.sub(r'^[\-\*]', '', text)

    # remove initial date (yyyy-mm-dd)
    if re.match(r'^\s*\d+-\d+-\d+\s+', text):
        text = re.sub(r'^\s*\d+-\d+-\d+\s+', '', text)

    # remove initial date (yy\date-of-year)
    if re.match(r'^\s*\d+/\d+\s+', text):
        text = re.sub(r'^\s*\d+/\d+\s+', '', text)

    # remove markdown links
    md_link = re.compile(r'\[(.*)\]\(.*\)')
    has_link = md_link.search(text)
    if has_link:
        link_name = md_link.findall(text)
        assert(len(link_name) == 1)
        text = re.sub(r'\[(.*)\]\(.*\)', link_name[0], text)

    return text


def get_todos():
    '''Get Tasks from todo list'''
    tasks = []

    if not CONFIGURATION.todo_file or \
       not os.path.exists(CONFIGURATION.todo_file):
        return tasks

    try:
        with open(CONFIGURATION.todo_file, 'r') as cfile:
            todo_start_tag = CONFIGURATION.todo_start_tag
            todo_stop_tag = CONFIGURATION.todo_stop_tag

            got_stop_tag = lambda line: todo_stop_tag and todo_stop_tag in line.lower()
            got_empty_line = lambda line: len(line.strip()) == 0

            if todo_start_tag:
                reading = False
                tid = 0
                for line in cfile.readlines():
                    line = line.rstrip()

                    if todo_start_tag in line.lower():
                        reading = True
                        continue

                    if reading and \
                       (got_stop_tag(line) or got_empty_line(line)):
                        reading = False
                        break

                    if reading:
                        line = sanitize(line)
                        tid += 1
                        tasks.append(Task(name=line, tid=tid))
            else:
                tasks = [
                    Task(name=sanitize(line), tid=lineno + 1)
                    for lineno, line in enumerate(cfile.readlines())
                ]
    except(TypeError, AttributeError, IOError) as error:
        LOGGER.error("could not get todo list: {}".format(error))
    return tasks


def get_tasks(condition=None, todos=None):
    '''Get all tasks that meet the condition'''

    if todos:
        tasks = todos
    else:
        tasks = get_todos()

    try:
        uids = dict()
        tid = len(tasks)

        with open(CONFIGURATION.data_fullpath) as cfile:
            for line in reversed(cfile.readlines()):
                fields = line.strip().split(',')
                if not fields[1]:
                    continue

                fields_n = len(fields)
                name, start_str, end_str = fields[1:4]

                # Take care of old history format with 5 fields
                if fields_n == 5:
                    start_str, end_str = fields[3:5]
                elif fields_n != 4:
                    raise Exception("History unexpected fields: {}: {}"
                                    .format(fields_n, fields))

                name = sanitize(name)
                task = Task(name=name, start_str=start_str, end_str=end_str)

                if task.uid not in uids:
                    tid += 1
                    uids[task.uid] = task.tid = tid
                else:
                    task.tid = uids[task.uid]

                tasks.append(task)

        return list(filter(condition, tasks))
    except IOError as error:
        LOGGER.debug("could not get tasks history: %s", error)
        return list()


def group_task_by(tasks, group=None):
    '''Group given task by name or date'''
    if group == 'name':
        uniques = []
        for task in tasks:
            if task not in uniques:
                uniques.append(task)

        for main_task in uniques:
            work_time_in_seconds = sum([
                same_task.work_time.seconds for same_task in tasks
                if same_task == main_task
            ])
            work_time = timedelta(seconds=work_time_in_seconds)
            main_task.work_time = work_time
        return uniques

    if group == 'date':
        task_map = {}
        for task in tasks:
            print(task)
            date = task.last_end_date
            if date in task_map.keys():
                task_map[date].append(task)
            else:
                task_map[date] = [task]
        return task_map
    else:
        LOGGER.warn('Could not group tasks by: ' + group)
        return tasks


def report_task(tasks, cfilter=None, title=None,
                detailed=False, todos=False, ascii=False):
    '''Visual task report'''
    tot_work_time = timedelta()

    if detailed:
        table_data = [['ID', 'Date', 'Interval', 'Tracked', 'Description']]
    elif todos:
        table_data = [['ID', 'Tracked', 'Description']]
    else:
        table_data = [['ID', 'Last time', 'Tracked', 'Description']]

    for task in tasks:
        tot_work_time += task.work_time

        if task.last_end_date:
            last_time = task.last_end_date
        else:
            last_time = ''

        time = strfdelta(task.work_time, fmt='{H:2}h {M:02}m')

        if detailed:
            interval = '{begin} -> {end}'.\
                       format(begin=task.start_time.strftime('%H:%M'),
                              end=task.end_time.strftime('%H:%M'))
            row = [paint(task.tid),
                   paint(last_time),
                   paint(interval),
                   paint(time),
                   paint(task.name)]
        elif todos:
            row = [paint(task.tid),
                   paint(time),
                   paint(task.name)]
        else:
            row = [paint(task.tid),
                   paint(last_time),
                   paint(time),
                   paint(task.name)]

        table_data.append(row)

    if ascii:
        table = AsciiTable(table_data)
    else:
        table = SingleTable(table_data)

    info('')
    print(table.table)
    info('')
    if cfilter:
        info('{filter}: Tracked time {time}'.format(
            filter=cfilter, time=strfdelta(tot_work_time)))
    else:
        info('Tracked time {time}'.format(time=strfdelta(tot_work_time)))


def do_report(args):
    '''Wrap show reports'''
    pattern = args['<pattern>']

    if args['todo']:
        todos = get_todos()
        if not todos:
            LOGGER.error('Could not find any Todos')
            return

        names = [t.name for t in todos]

        in_todo_list = lambda x: x.name in names
        tasks = get_tasks(in_todo_list, todos=todos)
        tasks = group_task_by(tasks, 'name')
        report_task(tasks, todos=True, ascii=args['--ascii'])
        return

    if args['today']:
        pattern = datetime.strftime(datetime.today(), '%Y-%m-%d')

    elif args['yesterday']:
        yesterday = datetime.today() - timedelta(1)
        # keep only the part with YYYY-MM-DD
        pattern = str(yesterday).split()[0]

    if args['--day-by-day']:
        by_end_date = lambda x: not pattern or (pattern in str(x.last_end_date) or pattern in str(x.name))
        task_map = group_task_by(get_tasks(by_end_date, todos=list()), 'date')

        for key in sorted(task_map.keys()):
            if not key:
                continue

            task = group_task_by(task_map[key], 'name')
            sorted_by_time = sorted(task,
                                    key=lambda x: x.work_time,
                                    reverse=True)

            report_task(sorted_by_time)
        return
    elif args['all'] or pattern:
        by_name_or_end_date = lambda x: not pattern or \
            (pattern in str(x.last_end_date) or pattern in x.name)

        tasks = get_tasks(by_name_or_end_date)

    else:
        # Just see if there is something running
        Task.status()
        return

    # By default show Task grouped by name
    if not args['--detailed']:
        tasks = group_task_by(tasks, 'name')
    else:
        # Otherwise show detailed report ordered
        # by time
        tasks.reverse()

    report_task(tasks, detailed=args['--detailed'], ascii=args['--ascii'])


def guess_task_id_from_string(task_name):
    '''Get task ID from task name'''
    guess_id = 0

    if len(task_name) == 1:
        task_name = task_name[0]
        try:
            guess_id = int(task_name)
        except ValueError:
            return False
    else:
        return False

    return guess_id


def do_config(args):
    '''Wrapper for configuration changes'''
    if args['data.directory']:
        CONFIGURATION.data_directory = args['<fullpath>']

    elif args['todo.file']:
        CONFIGURATION.todo_file = args['<fullpath>']

    elif args['todo.start_tag']:
        CONFIGURATION.todo_start_tag = args['<tag>']

    elif args['todo.stop_tag']:
        CONFIGURATION.todo_stop_tag = args['<tag>']

    elif args['autocomplete']:
        autocomplete()
    else:
        pass


def main():
    global RAFFAELLO
    args = docopt.docopt(__doc__)

    if args['--no-color']:
        LOGGER.debug("disabling color")
        RAFFAELLO = None

    if args['do']:
        if args['<name>']:
            name = args['<name>']
            if Task.get_running():
                info("Another task is already running")
                return

            if name == ['last']:
                last_task = get_tasks(todos=list())[0]
                Task(name=last_task.name, start_str=args['--time']).start()
                return

            # Check whether the given task name is actually a task id
            tid = guess_task_id_from_string(name)
            if tid is not False:
                work_on(task_id=tid, start_time_str=args['--time'])
                return

            new_task_name = ' '.join(args['<name>'])
            Task(new_task_name, start_str=args['--time']).start()
            return

    if args['edit']:
        task = Task.get_running()
        if not task:
            info('No task running')
            return
        edit_command = '{editor} {filename}'\
                       .format(editor=os.getenv('EDITOR'),
                               filename=CONFIGURATION.task_fullpath)
        os.system(edit_command)
        return

    if args['cancel']:
        Task.cancel()
        return

    if args['stop']:
        Task.stop(args['--time'])
        return

    if args['goto']:
        name = args['<newtask>']
        tid = guess_task_id_from_string(name)
        if tid is not False:
            tasks = get_tasks(lambda x: x.tid == tid)

            if not tasks:
                LOGGER.error("Could not find tasks with id {tid}".format(tid=tid))
                return
            else:
                task = tasks[0]
                new_task_name = task.name
        else:
            new_task_name = ' '.join(name)

        Task.stop()
        Task(new_task_name).start()
        return

    if args['see']:
        if args['config']:
            info(CONFIGURATION)
            return

        return do_report(args)

    if args['config']:
        do_config(args)
        return

    # Default, if a task is running show it
    if Task.get_running():
        Task.status()
        return

    # Default do_report
    if not args['<name>']:
        args['<name>'] = ['unknown']

    return do_report(args)


if __name__ == '__main__':
    main()
