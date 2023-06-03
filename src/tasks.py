"""
Tasks module: provides functions for managing tasks.

This module contains functions for creating, updating, and deleting tasks.
"""

import os
import json
import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from log import LOGGER
from configuration import get_task_file_path, get_history_file_path
from timetoolkit import str2datetime


@dataclass
class Task:
    """
    Class representing a task.

    Attributes
    ----------
    uid : str
        Unique ID of the task, generated using uuid.uuid4().
    description: str
        String describing the task
    start_str : str, optional
        String representation of the task start time in ISO format (YYYY-MM-DDTHH:MM:SS).
    stop_str : str, optional
        String representation of the task stop time in ISO format (YYYY-MM-DDTHH:MM:SS).
    """

    description: str
    start_str: str = None
    stop_str: str = None
    uid: str = field(default_factory=uuid.uuid4)
    start: datetime = field(default=None)
    stop: datetime = field(default=None)
    work: datetime = field(init=False, default=None)

    def __post_init__(self):
        if not self.start:
            self.start = str2datetime(self.start_str)
        if not self.stop:
            self.stop = tr2datetime(self.stop_str)

        if self.start > self.stop:
            msg = f"start ({self.start}) cannot be newer than stop ({self.stop}) in Task {self}"
            LOGGER.error(msg)
            return

        self.work = self.stop - self.start


def is_task_running() -> bool:
    """
    Check if there is a task currently running.

    Returns:
    --------
    bool
        True if a task is currently running, False otherwise.
    """
    return os.path.exists(get_task_file_path())


def start_task(task: Task) -> (bool, Task):
    """
    Start a Task if no task is running
    """
    if is_task_running():
        return False, get_task_running()

    try:
        with open(get_task_file_path(), "w") as file:
            data = {
                "description": task.description,
                "start": task.start.strftime("%Y-%m-%d %H:%M"),
                "uid": str(task.uid),
            }
            json.dump(data, file)
    except IOError as error:
        LOGGER.error("could not save task data: %s", error)
        return False, None

    return True, task


def get_task_running() -> Task:
    """
    Return the running task in a Task object or None if no task is running
    """

    if not is_task_running():
        return None

    with open(get_task_file_path(), "r", encoding="utf-8") as cfile:
        data = json.load(cfile)
        return Task(
            description=data["description"], start_str=data["start"], uid=data["uid"]
        )


def cancel_task() -> Task:
    """Cancel a running task"""

    task = get_task_running()
    if not task:
        return None

    os.remove(get_task_file_path())
    return task


def stop_task(stop_time=None) -> Task:
    """Stop a running task"""

    task = cancel_task()
    if not task:
        return None

    stopped_task = Task(
        description=task.description,
        start_str=task.start_str,
        stop_str=stop_time,
        uid=task.uid,
    )

    return stopped_task


class TaskOld(object):
    """Class representing a running task"""

    def __init__(self, name, start_str=None, end_str=None, tid=None):
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
    def last_end_date(self) -> str:
        """The last day when this Task was active"""
        if self.end_time:
            return self.end_time.strftime("%Y-%m-%d")
        return None

    @staticmethod
    def __is_running() -> bool:
        if os.path.exists(get_task_file_path()):
            LOGGER.debug("a task is running")
        else:
            LOGGER.debug("no task running")
        return os.path.exists(get_task_file_path())

    @staticmethod
    def get_running() -> "Task":
        """Check whether a task is running"""
        if not Task.__is_running():
            return None

        with open(get_task_file_path(), "r", encoding="utf-8") as cfile:
            data = json.load(cfile)
            return Task(data["name"], data["start"])

    @staticmethod
    def stop(stop_time_str=None):
        """Stop a running task"""
        task = Task.get_running()
        if not task:
            LOGGER.info("No task running")
            return

        # Get strings for the task report
        if stop_time_str:
            stop_time = str2datetime(stop_time_str)
            if stop_time < task.start_time:
                msg = f"stop time ({stop_time}) is more recent than start time ({task.start_time})"
                LOGGER.warning(msg)
            date = stop_time.strftime("%Y-%m-%d")
        else:
            stop_time = datetime.now()
            date = datetime.today()

        start_time_str = str(task.start_time).split(".")[0][:-3]
        stop_time_str = str(stop_time).split(".")[0][:-3]

        report_line = f"{date},{task.name},{start_time_str},{stop_time_str}\n"

        try:
            with open(get_history_file_path(), mode="a", encoding="utf-8") as cfile:
                cfile.writelines(report_line)
        except IOError as error:
            LOGGER.error("Could not save report: %s", error)

        # Delete current task data to mark it as stopped
        os.remove(get_task_file_path())

    @staticmethod
    def cancel() -> str:
        """Interrupt task without saving it in history"""
        task = Task.get_running()
        if task:
            with open(get_task_file_path(), "r", encoding="utf-8") as f:
                content = f.read()
            os.remove(get_task_file_path())
            return content
        return None

    @staticmethod
    def status() -> (bool, str):
        """Get status of current running task"""
        task = Task.get_running()
        if task:
            now = datetime.now()
            time = str(now - task.start_time).split(".")[0]
            hours, minutes, seconds = time.split(":")
            msg = f"Working on '{task.name}' for {hours}h {minutes}m {seconds}s"
            return True, msg
        return False, "No task running"

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
