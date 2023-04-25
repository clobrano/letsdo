import os
import re
import json
import hashlib
from datetime import datetime, timedelta

from log import LOGGER, RAFFAELLO
from configuration import get_configuration, get_task_file_path, get_history_file_path
from timetoolkit import str2datetime


def _p(msg):
    """Colorize message"""
    if msg and get_configuration()["color"] and RAFFAELLO:
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
        """The last day when this Task was active"""
        if self.end_time:
            return self.end_time.strftime("%Y-%m-%d")
        return None

    @staticmethod
    def __is_running():
        if os.path.exists(get_task_file_path()):
            LOGGER.debug("a task is running")
        else:
            LOGGER.debug("no task running")
        return os.path.exists(get_task_file_path())

    @staticmethod
    def get_running():
        """Check whether a task is running"""
        if Task.__is_running():
            with open(get_task_file_path(), "r", encoding="utf-8") as cfile:
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
            with open(get_history_file_path(), mode="a", encoding="utf-8") as cfile:
                cfile.writelines(report_line)
        except IOError as error:
            LOGGER.error("Could not save report: %s", error)
            return None

        # Delete current task data to mark it as stopped
        os.remove(get_task_file_path())

        hours, minutes = work_time_str.split(":")
        return (hours, minutes)

    @staticmethod
    def cancel():
        """Interrupt task without saving it in history"""
        task = Task.get_running()
        if task:
            with open(get_task_file_path(), "r", encoding="utf-8") as f:
                content = f.read()
            os.remove(get_task_file_path())
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
            with open(get_task_file_path(), "w") as cfile:
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
