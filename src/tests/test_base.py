#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for letsdo"""
import os
import unittest
from time import sleep
from datetime import timedelta

from tasks import Task
from configuration import (
    create_default_configuration,
    get_configuration,
    get_task_file_path,
    get_history_file_path,
    CONFIG_FILE_NAME
)
from app import work_on
from app import group_task_by
from app import get_tasks


class TestLetsdo(unittest.TestCase):
    """Test class"""

    def setUp(self):
        self.config_file = os.path.join("~", CONFIG_FILE_NAME)
        create_default_configuration()
        self.conf = get_configuration()

    def tearDown(self):
        if os.path.exists(get_history_file_path()):
            os.remove(get_history_file_path())
        if os.path.exists(get_task_file_path()):
            os.remove(get_task_file_path())
        if os.path.exists(self.config_file):
            os.remove(self.config_file)

    def test_group_task_by(self):
        """Test group_task_by"""
        task = Task("group 1", start_str="15:00").start()
        task.stop("15:05")

        task = Task("group 2", start_str="16:00").start()
        task.stop("16:01")

        task = Task("group 1", start_str="16:02").start()
        task.stop("16:03")

        real = group_task_by(get_tasks(), "name")
        self.assertEqual(len(real), 2)
        self.assertEqual(real[0].name, "group 1")
        self.assertEqual(real[0].work_time, timedelta(minutes=6))
        self.assertEqual(real[1].name, "group 2")
        self.assertEqual(real[1].work_time, timedelta(minutes=1))

    def test_continue_task_by_index(self):
        """test continue_task_by_index"""
        for i in range(3):
            task = Task("task {id}".format(id=i))
            task.start()
            sleep(1)
            task.stop()
            sleep(1)

        work_on(task_id=2)
        task = Task.get_running()
        self.assertEqual("task 1", task.name)

    def test_get_no_context(self):
        """test get_no_context"""
        task = Task("project without a context")
        self.assertIsNone(task.context)

    def test_get_context(self):
        """test get_context"""
        task = Task("project with a @context")
        self.assertEqual(task.context, "@context")

    def test_get_no_tags(self):
        """test get_no_tags"""
        task = Task("project without tags")
        self.assertIsNone(task.tags)

    def test_get_tags(self):
        """test get_tags"""
        task = Task("project with +some +tags")
        self.assertEqual(task.tags, ["+some", "+tags"])

    def test_create_named_task(self):
        """test create_named_task"""
        task = Task("named")
        self.assertEqual(task.name, "named")

    def test_get_non_running_task(self):
        """test get_non_running_task"""
        if os.path.exists(get_task_file_path()):
            os.remove(get_task_file_path())
        task = Task.get_running()
        self.assertIsNone(task)

    def test_get_running_task(self):
        """test get_running_task"""
        if not os.path.exists(get_task_file_path()):
            Task("foo task").start()
        task = Task.get_running()
        self.assertIsNotNone(task)

    def test_stop_non_running_task(self):
        """test stop_non_running_task"""

        if os.path.exists(get_task_file_path()):
            os.remove(get_task_file_path())

        if not os.path.exists(get_history_file_path()):
            with open(get_history_file_path(), "w", encoding="utf-8") as file:
                file.write("")

        no_tasks = len(open(get_history_file_path(), encoding="utf-8").readlines())

        Task.stop()
        new_no_tasks = len(open(get_history_file_path(), encoding="utf-8").readlines())

        self.assertEqual(no_tasks, new_no_tasks)

    def test_stop_running_task(self):
        """test stop_running_task"""
        if not os.path.exists(get_task_file_path()):
            Task("foo task").start()
        if not os.path.exists(get_history_file_path()):
            with open(get_history_file_path(), "w", encoding="utf-8") as fdata:
                fdata.write("")
        no_tasks = len(open(get_history_file_path(), encoding="utf-8").readlines())

        Task.stop()
        new_no_tasks = len(open(get_history_file_path(), encoding="utf-8").readlines())

        self.assertFalse(os.path.exists(get_task_file_path()))
        self.assertEqual(no_tasks + 1, new_no_tasks)

    def test_start_task(self):
        """test start_task"""
        if os.path.exists(get_task_file_path()):
            os.remove(get_task_file_path())
        Task("foo task").start()
        self.assertTrue(os.path.exists(get_task_file_path()))

    def test_status_task(self):
        """test status_task"""
        if os.path.exists(get_task_file_path()):
            os.remove(get_task_file_path())
        Task("foo task").start()
        self.assertTrue(Task.status())

    def test_cancel_running_task(self):
        Task("foo task").start()
        content = Task.cancel()
        self.assertFalse(os.path.exists(get_task_file_path()))
        self.assertIn("foo task", content)

    def test_task_representation(self):
        task = Task(
            "task description", start_str="2022-06-05 11:34", end_str="2022-06-05 12:34"
        )
        representation = f"{task}"
        self.assertIn(
            "- 2022-06-05| 1:00:00 (11:34 -> 12:34) - task description", representation
        )

    def test_task_representation_with_tid(self):
        task = Task(
            "task description",
            start_str="2022-06-05 11:34",
            end_str="2022-06-05 12:34",
            tid=123,
        )
        representation = f"{task}"
        self.assertIn("[123:", representation)  # head of the massage
        self.assertIn(
            "- 2022-06-05| 1:00:00 (11:34 -> 12:34) - task description", representation
        )


if __name__ == "__main__":
    unittest.main()
