#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Usage:
    lets do     <name>... [--time=<time>]
    lets see    [all|config] [--detailed|--day-by-day] [--ascii| --dot-list] [-p|--project] [<query>...]
    lets edit
    lets cancel
    lets stop   [<time>...]
    lets goto   <newtask>...
    lets track  <name>...
    lets config
    lets autocomplete

options:
    -a, --ascii       Print report table in ASCII characters
    -t, --time=<time> Change the start/stop time of the task on the fly

examples:
    lets see            # show today's activities
    lets see yesterday  # show yesterday's activities
    lets see 2018-07    # show 2018 July's activities
    lets see last July  # same as above (if we're still in 2019)
    lets see +project   # show activities with +project tag (+project is autocompleted with TAB)
    lets see something  # show activities whose description has he word 'something'
    lets see this week
    lets see last month
    lets see 2019
    ...
"""

import os
import hashlib
import re
import json
from datetime import datetime, timedelta
import docopt
from terminaltables import SingleTable, AsciiTable
from log import LOGGER, RAFFAELLO
from configuration import Configuration, autocomplete
from timetoolkit import str2datetime, strfdelta


def _p(msg):
    """Colorize message"""
    if msg and Configuration().color_enabled and RAFFAELLO:
        return RAFFAELLO.paint(str(msg))
    return msg


class Task(object):
    """Class representing a running task"""

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
        self.start_time = start_str

        if end_str:
            self.end_time = str2datetime(end_str.strip())
            self.work_time = self.end_time - self.start_time
            self.week_no = self.end_time.strftime("%V")
        else:
            self.end_time = None
            self.work_time = timedelta()
            self.week_no = None

    @property
    def start_time(self):
        return self._start_time

    @start_time.setter
    def start_time(self, value):
        if value:
            self._start_time = str2datetime(value.strip())
        else:
            self._start_time = datetime.now()

    @property
    def last_end_date(self):
        """ The last day when this Task was active"""
        if self.end_time:
            return self.end_time.strftime("%Y-%m-%d")
        return None

    @staticmethod
    def __is_running():
        exists = os.path.exists(Configuration().task_fullpath)
        LOGGER.debug("Is a task running? {}".format(exists))
        return exists

    @staticmethod
    def get_running():
        """Check whether a task is running"""
        if Task.__is_running():
            with open(Configuration().task_fullpath, "r") as cfile:
                data = json.load(cfile)
                return Task(data["name"], data["start"])
        return None

    @staticmethod
    def stop(stop_time_str=None):
        """Stop task"""
        task = Task.get_running()
        if not task:
            print("No task running")
            return None

        # Get strings for the task report
        if stop_time_str:
            stop_time = str2datetime(stop_time_str)
            if stop_time < task.start_time:
                LOGGER.warning(
                    "Given stop time (%s) is more recent than start time (%s)",
                    stop_time,
                    task.start_time,
                )
                return None
            date = stop_time.strftime("%Y-%m-%d")
        else:
            stop_time = datetime.now()
            date = datetime.today()

        work_time_str = str(stop_time - task.start_time).split(".")[0][:-3]
        start_time_str = str(task.start_time).split(".")[0][:-3]
        stop_time_str = str(stop_time).split(".")[0][:-3]

        report_line = "{date},{name},{start_time},{stop_time}\n".format(
            date=date,
            name=task.name,
            start_time=start_time_str,
            stop_time=stop_time_str,
        )

        try:
            with open(Configuration().data_fullpath, mode="a") as cfile:
                cfile.writelines(report_line)
        except IOError as error:
            LOGGER.error("Could not save report: %s", error)
            return None

        # Delete current task data to mark it as stopped
        os.remove(Configuration().task_fullpath)

        hours, minutes = work_time_str.split(":")
        return (hours, minutes)

    @staticmethod
    def cancel():
        """Interrupt task without saving it in history"""
        task = Task.get_running()
        if task:
            with open(Configuration().task_fullpath, "r") as cfile:
                content = cfile.read()
            os.remove(Configuration().task_fullpath)
            return content
        return None

    @staticmethod
    def status():
        """Get status of current running task"""
        task = Task.get_running()
        if task:
            now = datetime.now()
            time = str(now - task.start_time).split(".")[0]
            hours, minutes, seconds = time.split(":")
            print(
                _p(
                    "Working on '{}' for {}h {}m {}s".format(
                        task.name, hours, minutes, seconds
                    )
                )
            )
            return True
        print("No task running")
        return False

    def start(self):
        """Start task"""
        if not Task.__is_running():
            if self.__create():
                return Task.get_running()

            LOGGER.error("Could not create new task")
            return False

        LOGGER.warning("Another task is running")
        return True

    def __hash(self):
        gen = hashlib.sha256(self.name.encode())
        return gen.hexdigest()

    def __create(self):
        try:
            with open(Configuration().task_fullpath, "w") as cfile:
                json_data = """{
    "name": %s,
    "start": %s
}
""" % (
                    json.dumps(self.name),
                    json.dumps(str(self.start_time)),
                )
                cfile.write(json_data)
                return True
        except IOError as error:
            LOGGER.error("Could not save task data: %s", error)
            return False

    def __parse_name(self, name):
        # Sanitizing name (commas are still used to separate infos and cannot
        # be used in task's name
        name = name.replace(",", " ")
        self.name = name
        # Storing contexts (@) and projects (+)
        matches = re.findall(r"@[\w\-_]+", name)
        if len(matches) == 1:
            self.context = matches[0]
        matches = re.findall(r"\+[\w\-_]+", name)
        if len(matches) >= 1:
            self.tags = matches

    def __repr__(self):
        start_str = "None"
        end_str = "None"
        work_str = "in progress"

        if self.start_time:
            start_str = "%s" % self.start_time.strftime("%H:%M")

        if self.end_time:
            end_str = "%s" % self.end_time.strftime("%H:%M")
            work_str = "%s" % str(self.work_time).split(".")[0]

        if self.tid is not None:
            return "[%d:%s] - %s| %s (%s -> %s) - %s" % (
                self.tid,
                self.uid,
                self.last_end_date,
                work_str,
                start_str,
                end_str,
                self.name,
            )

        return "[%s] - %s| %s (%s -> %s) - %s" % (
            self.uid,
            self.last_end_date,
            work_str,
            start_str,
            end_str,
            self.name,
        )

    def __eq__(self, other):
        return self.name == other.name

    def __ne__(self, other):
        return self.name != other.name


def work_on(task_id=0, start_time_str=None):
    """Start given task id"""
    tasks = get_tasks(condition=lambda x: x.tid == task_id)
    tasks = group_task_by(tasks, group="name")
    if not tasks:
        LOGGER.error("could not find task ID '%s'", task_id)
    else:
        task = tasks[0]
        start_time = None
        if start_time_str:
            date_str = datetime.strftime(datetime.today(), "%Y-%m-%d")
            start_time = date_str + " " + start_time_str

        Task(task.name, start_str=start_time).start()


def sanitize(text):
    """Remove symbols, dates and Markdown syntax from text"""
    # remove initial list symbol (if any)
    if re.match(r"^[\-\*]", text):
        text = re.sub(r"^[\-\*]", "", text)

    # remove initial date (yyyy-mm-dd)
    if re.match(r"^\s*\d+-\d+-\d+\s+", text):
        text = re.sub(r"^\s*\d+-\d+-\d+\s+", "", text)

    # remove initial date (yy\date-of-year)
    if re.match(r"^\s*\d+/\d+\s+", text):
        text = re.sub(r"^\s*\d+/\d+\s+", "", text)

    # remove markdown links
    md_link = re.compile(r"\[(.*)\]\(.*\)")
    has_link = md_link.search(text)
    if has_link:
        link_name = md_link.findall(text)
        text = re.sub(r"\[(.*)\]\(.*\)", link_name[0], text)

    return text


def get_tasks(condition=None):
    """Get all tasks by condition"""
    tasks = []

    tid = 0
    uids = dict()
    try:
        with open(Configuration().data_fullpath) as cfile:
            for line in reversed(cfile.readlines()):
                fields = line.strip().split(",")
                if not fields[1]:
                    continue

                # Take care of old history format with worked_time
                if len(fields) == 5:
                    task = Task(
                        name=sanitize(fields[1]), start_str=fields[3], end_str=fields[4]
                    )
                elif len(fields) == 4:
                    task = Task(
                        name=sanitize(fields[1]), start_str=fields[2], end_str=fields[3]
                    )
                else:
                    raise Exception(
                        "History unexpected fields ({}: {})".format(len(fields), fields)
                    )

                # Tasks with same UID share the same Task ID as well
                # Integer IDs are easier to use than hash IDs
                if task.uid not in uids:
                    tid += 1
                    uids[task.uid] = tid
                task.tid = uids[task.uid]
                tasks.append(task)

        conditioned = filter(condition, tasks)
        return list(conditioned)
    except IOError as error:
        LOGGER.error("could not get tasks' history: %s", error)
        return []


def group_task_by(tasks, group=None):
    """Group given task by name or date"""
    if group == "name":
        uniques = []
        for task in tasks:
            if task not in uniques:
                uniques.append(task)

        for main_task in uniques:
            work_time_in_seconds = sum(
                [
                    same_task.work_time.seconds
                    for same_task in tasks
                    if same_task == main_task
                ]
            )
            work_time = timedelta(seconds=work_time_in_seconds)
            main_task.work_time = work_time
        return uniques

    if group == "date":
        task_map = {}
        for task in tasks:
            date = task.last_end_date
            if date in task_map.keys():
                task_map[date].append(task)
            else:
                task_map[date] = [task]
        return task_map

    LOGGER.warning("Could not group tasks by: %s", group)
    return tasks


def report_task(tasks, title=None, detailed=False, ascii=False):
    """Display table with tasks data"""

    table_data = [["ID", "Last update", "Work time", "Description"]]
    if detailed:
        table_data = [["ID", "Last update", "Work time", "Interval", "Description"]]
        tasks = sorted(tasks, key=lambda x: x.end_time, reverse=True)

    tot_work_time = timedelta()
    for task in tasks:
        tot_work_time += task.work_time

    for task in tasks:
        last_time = ""
        if task.last_end_date:
            if task.tid != "R":
                last_time = task.end_time.strftime("%d-%m-%Y w%V")
            else:
                last_time = task.start_time.strftime("%Y-%m-%d %H:%M")

        perc = 0
        if tot_work_time > timedelta(0):
            perc = int((task.work_time / tot_work_time) * 100)

        time = "{} {:2d}%".format(
            strfdelta(task.work_time, fmt="{H:2}h {M:02}m"), perc
        )

        # smart break message at boundaries
        task_name = task.name
        if len(task.name) > 53:
            word_break = task_name.find(" ", 45)
            if word_break == -1:
                word_break = 45
            task_name = task_name[:word_break] + "\n ⤷" + task_name[word_break:]

        if detailed:
            begin = task.start_time.strftime("%H:%M")
            end = task.end_time.strftime("%H:%M")
            interval = "{} -> {}".format(begin, end)

            row = [_p(task.tid), _p(last_time), _p(time), _p(interval), _p(task_name)]
        else:
            row = [_p(task.tid), _p(last_time), _p(time), _p(task_name)]

        table_data.append(row)

    if len(tasks) == 0:
        print(_p("Nothing to show for %s" % title))
        return

    if title:
        title = " %s " % title

    if len(tasks) > 1:
        recap = "activities,"
    else:
        recap = "activity,"
    table_data.append(
        [
            len(tasks),
            recap,
            "total time:",
            _p(strfdelta(tot_work_time, fmt="{D:2}d {H:2}h {M:02}m")),
        ]
    )

    if ascii:
        table = AsciiTable(table_data, title)
    else:
        table = SingleTable(table_data, title)

    table.outer_border = True
    table.inner_column_border = False
    table.inner_heading_row_border = True
    table.inner_footing_row_border = True
    table.justify_columns[0] = "right"
    table.justify_columns[1] = "center"
    table.justify_columns[2] = "right"
    table.justify_columns[3] = "left"

    print("")
    print(table.table)


def __is_a_month(string):
    months = [
        "jan",
        "feb",
        "mar",
        "apr",
        "may",
        "jun",
        "jul",
        "aug",
        "sep",
        "oct",
        "nov",
        "dec",
    ]
    if string.lower() in months:
        return True

    for month in months:
        if month in string.lower():
            return True

    return False


def __get_time_format_from_query(query):
    format = "%Y-%m-%d"

    if not query:
        return format

    if "last year" in query:
        format = "%Y"
    elif "week" in query:
        format = "%V"
        week_check = True
    elif "month" in query or __is_a_month(query):
        format = "%Y-%m"

    return format


def __get_task_condition_from_query(query):
    format = __get_time_format_from_query(query)
    try:
        query = datetime.strftime(str2datetime(query), format)
    except:
        LOGGER.debug("query '%s' does not seems a date", query)

    if format == "%V":
        condition = lambda x: x.week_no == query and x.end_time.strftime(
            "%Y"
        ) == datetime.now().strftime("%Y")
    else:
        condition = lambda x: not query or (
            query in str(x.last_end_date) or query in x.name
        )

    return condition, query, format


def do_report(args):
    """Wrap show reports"""

    if not args["all"] and not args["<query>"]:
        args["<query>"] = "today"

    query = args["<query>"]

    condition, date, format = __get_task_condition_from_query(query)

    if format == "%V":
        title = "week {}".format(date)
    else:
        title = "{}".format(date)

    tasks = get_tasks(condition)

    if args["--detailed"]:
        tasks.reverse()
        report_task(tasks, title=title, detailed=True, ascii=args["--ascii"])
        return

    if args["--day-by-day"]:
        task_map = group_task_by(tasks, "date")

        for key in sorted(task_map.keys()):
            if not key:
                continue

            task = group_task_by(task_map[key], "name")
            sorted_by_time = sorted(task, key=lambda x: x.work_time, reverse=True)

            report_task(sorted_by_time)
        return

    tasks = group_task_by(tasks, "name")
    if args["--dot-list"]:
        print(_p("\n{}".format(title)))

        for task in tasks:
            print(_p(" ● (%s) %s" % (task.tid, task.name)))
        return

    running = Task.get_running()
    current_running = ["today", "now", "this week", "this month"]
    if running and (
        not query or query.lower() in current_running or query in running.name
    ):
        running.tid = "R"
        running.work_time = datetime.now() - running.start_time
        running.end_time = running.start_time
        tasks.insert(0, running)

    report_task(tasks, title=title, detailed=args["--detailed"], ascii=args["--ascii"])


def guess_task_id_from_string(task_name):
    """Get task ID from task name"""
    guess_id = 0

    try:
        guess_id = int(task_name)
    except ValueError:
        return False

    return guess_id


def main():
    global RAFFAELLO
    args = docopt.docopt(__doc__)

    if args["autocomplete"]:
        autocomplete()
        return

    if args["do"]:
        if Task.get_running():
            print("Another task is already running")
            return 1

        if args["<name>"]:
            name = " ".join(args["<name>"])
            tid = None

            if name == "last":
                tid = 1
            else:
                tid = guess_task_id_from_string(name)

            if tid:
                work_on(task_id=tid, start_time_str=args["--time"])
            else:
                Task(name, start_str=args["--time"]).start()

            task = Task.get_running()
            start_time_str = task.start_time.strftime("%H:%M")
            print(_p("%s: started task \n ⤷  %s\n\n" % (start_time_str, task.name)))

            return 0

    if args["track"]:
        name = " ".join(args["<name>"])
        tid = None

        task = Task.get_running()
        if task:
            Task.cancel()

        Task(name, start_str=args["--time"]).start()
        Task.stop()
        print(_p("added task '%s' to today's list" % name))

        if task:
            task.start()

        return 0

    if args["edit"]:
        task = Task.get_running()
        if not task:
            print("No task running")
            return

        edit_command = "{editor} {filename}".format(
            editor=os.getenv("EDITOR"), filename=Configuration().task_fullpath
        )
        os.system(edit_command)
        return 0

    if args["config"]:
        edit_command = "{editor} {filename}".format(
            editor=os.getenv("EDITOR"),
            filename=os.path.join(os.path.expanduser("~"), ".letsdo"),
        )
        os.system(edit_command)
        return 0

    if args["cancel"]:
        content = Task.cancel()
        print("Cancelled task")
        print(_p(content))
        return 0

    if args["stop"]:
        task = Task.get_running()
        if not task:
            print("no task running")
            return 0

        work_time = Task.stop(" ".join(args["<time>"]))
        now = datetime.now().strftime("%H:%M")
        print(
            _p(
                "%s: stopped task: \n ⤷ %s\n\nafter %s hours, %s minutes\n\n"
                % (now, task.name, work_time[0], work_time[1])
            )
        )
        return 0

    if args["goto"]:
        name = " ".join(args["<newtask>"])

        tid = guess_task_id_from_string(name)
        if tid:
            tasks = get_tasks(lambda x: x.tid == tid)

            if not tasks:
                LOGGER.error("could not find tasks id %s", tid)
                return 1

            name = tasks[0].name

        task = Task.get_running()
        if task:
            work_time = Task.stop()
            print(
                _p(
                    "stopped task '%s' after %s hours, %s minutes"
                    % (task.name, work_time[0], work_time[1])
                )
            )

        task = Task(name)
        task.start()
        start_time_str = task.start_time.strftime("%H:%M")
        print(_p("Task [%s] started at %s" % (task.name, start_time_str)))
        return 0

    if args["see"]:
        if args["<query>"]:
            args["<query>"] = " ".join(args["<query>"])

        return do_report(args)

    # Default, if a task is running show it
    if Task.get_running():
        Task.status()
        return 0

    # Default do_report
    if not args["<name>"]:
        args["<name>"] = ["unknown"]

    return do_report(args)


if __name__ == "__main__":
    main()
