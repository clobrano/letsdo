# -*- coding: utf-8 -*-
# vi: set ft=python :
"""
The Handler module provides a simple way to redirect incoming requests to specific functions.
"""

import os
from datetime import datetime

from tasks import Task, start_task, stop_task, cancel_task
from app import get_tasks, store_task
from configuration import autocomplete

from history import CSVHistory


def autocomplete_handler():
    """handle autocomplete configuration request"""
    return autocomplete()


def start_task_handler(description: str, start_str: str) -> (bool, str):
    """handles a request to start a task"""
    if not start_str:
        start_str = datetime.now().strftime("%H:%M")

    task = Task(description, start_str=start_str)
    is_ok, new_task = start_task(task)
    if not is_ok:
        if not new_task:
            return False, f"could not start task {task}"
        return False, f"there is another task running: {task}"

    return True, f"{new_task} started"


def edit_file_handler(filename) -> (bool, str):
    """handles a request to edit a file with the system default editor"""
    if not os.path.exists(filename):
        return False, f"could not find {filename}"

    default_editor = os.getenv("EDITOR")
    edit_command = f"{default_editor} {filename}"
    os.system(edit_command)
    return True, ""


def cancel_task_handler() -> (bool, str):
    """handles a request to cancel the current task"""
    task = cancel_task()
    if task:
        return True, f"task {task} canceled"
    return False, "No task running, nothing to do"


def stop_task_handler(stop_time: str) -> (bool, str):
    """handles a request to stop the current task"""
    task = stop_task(stop_time)
    if not task:
        return False, "No task was running"
    now = datetime.now().strftime("%H:%M")
    msg = f"{now}: stopped task: {task.description}, after {task.work}"

    store_task(task)
    return True, msg


def goto_task_handler(tid: int) -> (bool, str):
    """handles a request to switch to another task given the ID"""
    tasks = get_tasks(lambda x: x.tid == tid)
    if not tasks:
        return False, f"could not find task with ID {tid}"
    task = tasks[0]

    now = datetime.now().strftime("%H:%M")
    is_ok, msg = stop_task_handler(now)
    if not is_ok:
        return False, msg
    return start_task_handler(task.name, now)


def get_tasks_by_query(query: str = None) -> list[Task]:
    """Get all tasks by condition"""
    return CSVHistory().get_tasks_by_query(query)
