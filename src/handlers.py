# -*- coding: utf-8 -*-
# vi: set ft=python :
"""
The Handler module provides a simple way to redirect incoming requests to specific functions.
"""

import os
from datetime import datetime
from app import Task, guess_task_id_from_string, work_on, get_tasks
from configuration import autocomplete, create_default_configuration


def autocomplete_handler():
    """handle autocomplete configuration request"""
    return autocomplete()


def start_task_handler(description: str, start_str: str="") -> (bool, str):
    """handles a request to start a task"""
    if not description:
        return False, "task description is mandatory"

    if Task.get_running():
        return False, "Another task is already running"

    if description == "last":
        tid, is_ok = 1, True
    else:
        tid, is_ok = guess_task_id_from_string(description)

    if is_ok:
        work_on(task_id=tid, start_time_str=start_str)
    else:
        Task(description, start_str=start_str).start()

    task = Task.get_running()
    return True, f"{task.start_time}: {task.name} started"


def edit_file_handler(filename) -> (bool, str):
    """handles a request to edit a file with the system default editor"""
    if not os.path.exists(filename):
        create_default_configuration()

    default_editor = os.getenv("EDITOR")
    edit_command = f"{default_editor} {filename}"
    os.system(edit_command)
    return True, ""


def cancel_task_handler() -> (bool, str):
    """handles a request to cancel the current task"""
    msg = Task.cancel()
    if not msg:
        return False, "No task running, nothing to do"
    return True, f"cancelled task: {msg}"


def stop_task_handler(stop_time: str) -> (bool, str):
    """handles a request to stop the current task"""
    task = Task.get_running()
    if not task:
        return False, "no task running, nothing to do"

    work_time = Task.stop(stop_time)
    if not work_time:
        return False, "error: could not get stop time"
    now = datetime.now().strftime("%H:%M")
    msg = f"{now}: stopped task: {task.name}, after {work_time[0]}hours, {work_time[1]} minutes"
    return True, msg


def goto_task_handler(description: str) -> (bool, str):
    """handles a request to switch to another task given the ID"""
    if not description:
        return False, "task description is mandatory"

    if Task.get_running():
        now = datetime.now().strftime("%H:%M")
        is_ok, msg = stop_task_handler(now)
        if not is_ok:
            return False, msg

    tid, got_id = guess_task_id_from_string(description)
    if got_id:
        work_on(task_id=tid)
        return True, ""
    else:
        return Task(description).start(), ""

