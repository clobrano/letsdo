#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Usage:
    lets see          [--no-color] [todo | all | today | yesterday] [--detailed | --day-by-day] [--ascii] [<pattern>]
    lets do           [--no-color] [--time=<time>] [<name>...]
    lets edit         [--no-color]
    lets goto         [--no-color] [<newtask>...]
    lets stop         [--no-color] [--time=<time>]
    lets cancel       [--no-color]
    lets last         [--no-color] [--time=<time>]
    lets autocomplete
    lets status       [--no-color]

options:
    --ascii                Print report table in ASCII characters (for VIM integration)
    -t, --time=<time>          Change the start/stop time of the task on the fly (to be used with to, stop)
    --no-color            Disable colorizer (see raffaello)
'''

import os
import docopt
import datetime
import sys
import re
from string import Formatter
import hashlib
import json
from terminaltables import SingleTable, AsciiTable
from log import info, err, warn, dbg, do_color
from configuration import Configuration
from timetoolkit import format_h_m, str2datetime, strfdelta

def paint(msg):
    if msg and do_color:
        return raf.paint(str(msg))
    return msg

class Task(object):
    def __init__(self, name=None, start_str=None, end_str=None, id=None):
        if not name:
            raise ValueError

        self.name = name.strip()
        self.id = id
        self.uid = None

        self.context = None
        self.tags = None
        self.parse_name(self.name)

        # Adjust Task's start time with a string representing a time or a date + time,
        # otherwise the task starts now.
        # See std2datetime for available formats.
        if start_str:
            self.start_time = str2datetime(start_str.strip())
        else:
            self.start_time = datetime.datetime.now()

        if end_str:
            self.end_time = str2datetime(end_str.strip())
            self.work_time = self.end_time - self.start_time
        else:
            self.end_time = None
            self.work_time = datetime.timedelta()

    @property
    def last_end_date (self):
        ''' The last day when this Task was active'''
        if self.end_time:
            return self.end_time.strftime('%Y-%m-%d')
        else:
            return None

    @staticmethod
    def __is_running():
        exists = os.path.exists(Configuration().task_fullpath)
        dbg('Is a task running? {}'.format(exists))
        return exists

    @staticmethod
    def get_running():
        if Task.__is_running():
            with open(Configuration().task_fullpath, 'r') as f:
                data = json.load(f)
                return Task(data['name'], data['start'])
        return None

    @staticmethod
    def stop(stop_time_str=None):
        task = Task.get_running()
        if not task:
            info('No task running')
            return

        # Get strings for the task report
        if stop_time_str:
            stop_time = str2datetime(stop_time_str)
            if stop_time < task.start_time:
                warn('Given stop time (%s) is more recent than start time (%s)'
                     % (stop_time, task.start_time))
                return False
            date = stop_time.strftime('%Y-%m-%d')
        else:
            stop_time = datetime.datetime.now()
            date = datetime.date.today()

        work_time_str = str(stop_time - task.start_time).split('.')[0][:-3]
        start_time_str = str(task.start_time).split('.')[0][:-3]
        stop_time_str = str(stop_time).split('.')[0][:-3]

        report_line = '{date},{name},,{start_time},{stop_time}\n'\
                .format(date=date,
                        name=task.name,
                        start_time=start_time_str,
                        stop_time=stop_time_str)

        try:
            with open(Configuration().data_fullpath, mode='a') as f:
                f.writelines(report_line)
        except IOError, e:
            err ('Could not save report: ' + err.message)
            return False

        # Delete current task data to mark it as stopped
        os.remove(Configuration().task_fullpath)

        hours, minutes = work_time_str.split(':')
        info('Stopped \'{name}\' [id: {hash}] after {h}h {m}m of work'.format(
            name=task.name, h=hours, m=minutes, hash=task.uid[:7]))

        return True

    @staticmethod
    def cancel():
        task = Task.get_running()
        if task:
            with open(Configuration().task_fullpath, 'r') as f:
                content = f.read()
            os.remove(Configuration().task_fullpath)
            info('Cancelled task [{id}]'.format(id=task.uid))
            info(content)

    @staticmethod
    def status():
        task = Task.get_running()
        if task:
            now = datetime.datetime.now()
            time = str(now - task.start_time).split('.')[0]
            hours, minutes, seconds = time.split(':')
            info('Working on \'{name}\' [id: {uid}] for {h}h {m}m {s}s'.format(
                name=task.name, h=hours, m=minutes, s=seconds, uid=task.uid[:7]))
            return True
        else:
            info('No task running')
            return False
    
    def start(self):
        if not Task.__is_running():
            if self.__create():
                return Task.get_running()

            err('Could not create new task')
            return False

        warn('Another task is running')
        return True

    def __create(self):
        try:
            with open(Configuration().task_fullpath, 'w') as f:
                json_data = '''{
    "name": %s,
    "start": %s
}
'''% (json.dumps(self.name), json.dumps(str(self.start_time)))
                f.write(json_data)
                info('Started task [%s]:' % self.uid[:7]);
                info(json_data);
                return True
        except IOError, err:
            err ('Could not save task data: ' + err.message)
            return False

    def parse_name(self, name):
        # Sanitizing name (commas are still used to separate infos and cannot
        # be used in task's name
        name = name.replace(',', ' ')
        self.name = name
        self.uid = hashlib.sha224(self.name).hexdigest()
        # Storing contexts (@) and projects (+)
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
            return '[%d] - %s| %s (%s -> %s) - [%s] %s' % (self.id, self.last_end_date,
                                                      work_str, start_str,
                                                      end_str, self.uid[:7], self.name)

        return '%s| %s (%s -> %s) - [%s] %s' % (self.last_end_date, work_str, start_str,
                                           end_str, self.uid[:7], self.name)

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

    To enable this feature do either of the following:
        - put letsdo_completion file under /etc/bash_completion.d/ for system-wide autocompletion
    or:
        - put letsdo_completion file in your home directory and "source" it in your .bashrc
        e.g.
            source /full/path/to/letsdo_completion

    Letsdo can copy the script in your $HOME for you if you replay with "Y" at this message, otherwise
    the letsdo_completion file will be printed out here and it is up to you to copy and save it
    as said above.

    Do you want Letsdo to copy the script in your $HOME directory? [Y/n]
    '''

    _ROOT = os.path.abspath(os.path.dirname(__file__))
    completion = os.path.join(_ROOT, 'letsdo_scripts', 'letsdo_completion')

    info(message)

    resp = raw_input()
    if resp.lower() == 'y':
        completionfile = os.path.join(
            os.path.expanduser(
                '~', ), '.letsdo_completion')
        with open(completionfile, 'w') as f:
            f.writelines(open(completion).read())
    else:
        print(
            '--- CUT HERE ------------------------------------------------------------------'
        )
        print(open(completion).read())


def work_on(task_id=0, start_time_str=None):
    tasks = get_tasks(condition=lambda x: x.id == task_id)
    tasks = group_task_by(tasks, group='name')
    if not tasks:
        err("Could not find any task with ID '{id}'".format(id=task_id))
    else:
        assert (len(tasks) == 1)
        task = tasks[0]
        start_time = None
        if start_time_str:
            date_str = datetime.datetime.strftime(datetime.datetime.today(),
                                                  '%Y-%m-%d')
            start_time = date_str + ' ' + start_time_str

        Task(task.name, start_str=start_time).start()


def sanitize(text, filters=[]):
    # remove initial list symbol (if any)
    if re.match('^[\-\*]', text):
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
        assert (len(link_name) == 1)
        text = re.sub('\[(.*)\]\(.*\)', link_name[0], text)

    return text


def get_todos():
    tasks = []
    try:
        with open(Configuration().todo_fullpath, 'r') as f:
            todo_start_tag = Configuration().todo_start_tag
            todo_stop_tag = Configuration().todo_stop_tag

            got_stop_tag = lambda line: todo_stop_tag and todo_stop_tag in line.lower()
            got_empty_line = lambda line: len(line.strip()) == 0


            if todo_start_tag:
                reading = False
                id = 0
                for line in f.readlines():
                    line = line.rstrip()

                    if todo_start_tag in line.lower():
                        reading = True
                        continue

                    if reading and (got_stop_tag(line) or got_empty_line(line)):
                        reading = False
                        break

                    if reading:
                        line = sanitize(line)
                        id += 1
                        tasks.append(Task(name=line, id=id))
            else:
                tasks = [
                    Task(name=sanitize(line), id=lineno + 1)
                    for lineno, line in enumerate(f.readlines())
                ]
    except (TypeError, AttributeError, IOError):
        dbg("Could not get todo list. Todo file not set or incorrect.")
    return tasks


def get_tasks(condition=None, todos=[]):
    datafilename = Configuration().data_fullpath

    # Some todos might have been logged yet and some other don't.
    # Pass this list to avoid duplication, but I do not like
    # this solution
    if todos:
        tasks = todos
    elif todos == []:
        tasks = get_todos()
    else:
        # Skip todos loading
        tasks = []

    id = len(tasks)
    try:
        with open(datafilename) as f:
            for line in reversed(f.readlines()):
                dbg(line)
                fields = line.strip().split(',')
                if not fields [1]:
                    continue
                # Take care of old history format with worked_time
                if len(fields) == 5:
                    t = Task(name=sanitize(fields[1]), start_str=fields[3], end_str=fields[4])
                elif len(fields) == 4:
                    t = Task(name=sanitize(fields[1]), start_str=fields[2], end_str=fields[3])
                else:
                    raise Exception ("History has unexpected number of fields ({num_fields}: {fields})".format (
                        num_fields=len(fields),
                        fields=fields))

                # If a task with the same name exists,
                # keep the same ID as well
                try:
                    same_task = tasks.index(t)
                    t.id = tasks[same_task].id
                    dbg('{task_name} has old id {id}'.format(
                        task_name=t.name, id=t.id))
                except ValueError:
                    id += 1
                    t.id = id
                    dbg('{task_name} has new id {id}'.format(
                        task_name=t.name, id=t.id))
                tasks.append(t)

        return filter(condition, tasks)
    except IOError:
        return []


def group_task_by(tasks, group=None):
    if group is 'name':
        uniques = []
        for task in tasks:
            if not task in uniques:
                uniques.append(task)

        for main_task in uniques:
            work_time_in_seconds = sum([
                same_task.work_time.seconds for same_task in tasks
                if same_task == main_task
            ])
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
        warn ('Could not group task by: ' + group);
        return tasks


def report_task(tasks, filter=None, title=None, detailed=False, todos=False, ascii=False):
    tot_work_time = datetime.timedelta()

    if detailed:
        table_data = [['ID', 'Date', 'Interval', 'Time', 'Task description']]
    elif todos:
        table_data = [['ID', 'Time', 'Task description']]
    else:
        table_data = [['ID', 'Last date', 'Time', 'Task description']]

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
            row = [ paint(task.id),
                    paint(last_time),
                    paint(interval),
                    paint(time),
                    paint(task.name)]
        elif todos:
            row = [ paint(task.id),
                    paint(time),
                    paint(task.name)]
        else:

            row = [ paint(task.id),
                    paint(last_time),
                    paint(time),
                    paint(task.name)]

        table_data.append(row)

    if ascii:
        table = AsciiTable(table_data)
    else:
        table = SingleTable(table_data)

    if title:
        table.title = title
    else:
        table.title = filter

    info('')
    print(table.table)
    info('')
    if filter:
        info('{filter}: Total work time {time}'.format(
            filter=filter, time=strfdelta(tot_work_time)))
    else:
        info('Total work time {time}'.format(
            filter=filter, time=strfdelta(tot_work_time)))


def report_full(filter=None):
    tasks = {}
    datafilename = Configuration().data_fullpath
    with open(datafilename) as f:
        for id, line in enumerate(f.readlines()):
            line = line.strip()
            tok = line.split(',')
            if not filter or (filter in tok[4] or filter in tok[1]):
                dbg('accepting %s' % line)
                task = Task(name=tok[1], start_str=tok[3], end_str=tok[4], id=id)
                date = task.last_end_date
                if date in tasks.keys():
                    tasks[date].append(task)
                else:
                    tasks[date] = [task]

        if len(tasks) == 0:
            info('No tasks found with filter \'{filter}\''.format(
                filter=filter))
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

                column += '%s | %s -> %s = %s | %s' % (task.last_end_date,
                                                       start_str, end_str,
                                                       work_str, task.name)
                column += '\n'

            print('-' * 60)
            print(column)
            print('Work: {wtime},  Break: {btime}'.format(
                wtime=tot_time, btime=pause))
            print('')

        return tot_time, pause


def do_report(args):
    pattern = args['<pattern>']
    title=None

    if args['today']:
        title="Today's Tasks "
        today_date = datetime.datetime.strftime(datetime.datetime.today(),
                                                '%Y-%m-%d')
        by_logged_today = lambda x: today_date in str(x.last_end_date)
        tasks = get_tasks(by_logged_today)

    elif args['--day-by-day']:
        title = ""
        if pattern:
            title = ": by pattern < {pattern} > ".format(pattern=pattern)
        by_end_date = lambda x: not pattern or (pattern in str(x.last_end_date) or pattern in str(x.name))
        map = group_task_by(get_tasks(by_end_date), 'date')

        for key in sorted(map.keys()):
            if not key:
                continue
            t = group_task_by(map[key], 'name')
            sorted_by_time = sorted (t, key=lambda x: x.work_time, reverse=True)
            report_task(sorted_by_time, title=key + title)
        return
    elif args['yesterday']:
        title="Yesterday's Tasks "
        yesterday = datetime.datetime.today() - datetime.timedelta(1)
        yesterday_date = str(yesterday).split()[0]  # keep only the part with YYYY-MM-DD
        by_logged_yesterday = lambda x: yesterday_date in str(x.last_end_date)
        tasks = get_tasks(by_logged_yesterday)
    else:  # Defaults on all tasks
        if not pattern:
            info ("Do you really want to see ALL tasks (it might be a looong list) [Y/n]? (hint: for today's task just add today flag)")
            resp = raw_input()
            if resp.lower() == 'n' or resp.lower() == 'no':
                return
        title="All Tasks and Todos "
        by_name_or_end_date = lambda x: not pattern or (pattern in str(x.last_end_date) or pattern in x.name)
        tasks = get_tasks(by_name_or_end_date)

    # By default show Task grouped by name
    if args['--detailed']:
        tasks.reverse()
    else:
        tasks = group_task_by(tasks, 'name')

    report_task(tasks, title=title, detailed=args['--detailed'], ascii=args['--ascii']);

def guess_task_id_from_string (task_name):
    guess_id = 0

    if len(task_name) == 1:
        task_name = task_name [0]
        try:
            guess_id = int (task_name)
        except ValueError:
            return False
    else:
        return False

    return guess_id


def main():
    global do_color
    args = docopt.docopt(__doc__)

    if not args['--no-color']:
        do_color = False

    if args['do']:
        if args['<name>']:
            name = args['<name>']
            if Task.get_running():
                info ("Another task is already running")
                return
            # Check whether the given task name is actually a task ID
            id = guess_task_id_from_string (name)
            if id != False:
                work_on(task_id=id, start_time_str=args['--time'])
                return
            new_task_name = ' '.join(args['<name>'])
            Task(new_task_name, start_str=args['--time']).start()
            return

    if args['edit']:
        task = Task.get_running()
        if not task:
            info ('No task running')
            return
        edit_command = '{editor} {filename}'\
                .format(editor=os.getenv('EDITOR'),
                        filename=Configuration().task_fullpath)
        os.system(edit_command)
        return

    if args['cancel']:
        Task.cancel()
        return

    if args['last']:
        last_task = get_tasks(todos=None)[0]
        Task(name=last_task.name, start_str=args['--time']).start();
        return

    if args['todo']:
        todos = get_todos()
        if (len(todos) == 0):
            info ('Could not find any Todos');
            return

        names = [t.name for t in todos]

        in_todo_list = lambda x: x.name in names
        tasks = get_tasks(in_todo_list, todos=todos)
        tasks = group_task_by(tasks, 'name')
        report_task(tasks, todos=True, title="Todos", ascii=args['--ascii'])
        return

    if args['stop']:
        Task.stop(args['--time'])
        return

    if args['goto']:
        name = args['<newtask>']
        id = guess_task_id_from_string (name)
        if id != False:
            tasks = get_tasks(lambda x: x.id == id)

            if len(tasks) == 0:
                err("Could not find tasks with id '%d'" & id)
                return
            else:
                task = tasks[0]
                new_task_name = task.name
        else:
            new_task_name = ' '.join(name)

        Task.stop()
        Task(new_task_name).start()
        return

    if args['autocomplete']:
        autocomplete()
        return

    if args['see']:
        if args ['todo']:
            todos = get_todos()
            if (len(todos) == 0):
                info ('Could not find any Todos');
                return

            names = [t.name for t in todos]

            in_todo_list = lambda x: x.name in names
            tasks = get_tasks(in_todo_list, todos=todos)
            tasks = group_task_by(tasks, 'name')
            report_task(tasks, todos=True, title="Todos", ascii=args['--ascii'])
            return
        else:
            return do_report(args)

    # Default, if a task is running show it
    if Task.get_running():
        Task.status()
        return

    # Default do_report
    if not args['<name>']:
        args['<name>'] = ['unknown']

    if args ['see']:
        return do_report(args)


if __name__ == '__main__':
    main()
