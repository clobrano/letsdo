#!/usr/bin/env python
# -*- coding: utf-8 -*-
import unittest
import os
from letsdo.src.letsdo import Task
from letsdo.src.letsdo import TASK_FILENAME
from letsdo.src.letsdo import DATA_FILENAME

class TestLetsdo(unittest.TestCase):

    def test_create_unnamed_task(self):
        task = Task()
        self.assertEquals(task.name, 'unknown')

    def test_create_named_task(self):
        task = Task('named')
        self.assertEquals(task.name, 'named')

    def test_get_non_running_task(self):
        if os.path.exists(TASK_FILENAME):
            os.remove(TASK_FILENAME)
        task = Task.get()
        self.assertEquals(task, None)

    def test_get_running_task(self):
        if not os.path.exists(TASK_FILENAME):
            Task().start()
        task = Task.get()
        self.assertNotEquals(task, None)

    def test_change_non_running_task(self):
        if os.path.exists(TASK_FILENAME):
            os.remove(TASK_FILENAME)
        ret = Task.change('newname')
        self.assertEqual(ret, None)

    def test_change_running_task(self):
        if not os.path.exists(TASK_FILENAME):
            Task().start()
        Task.change('newname')
        self.assertEqual(Task.get().name, 'newname')

    def test_stop_non_running_task(self):
        if os.path.exists(TASK_FILENAME):
            os.remove(TASK_FILENAME)
        if not os.path.exists(DATA_FILENAME):
            with open(DATA_FILENAME, mode='w') as f:
                f.write('')
        no_tasks = len(open(DATA_FILENAME).readlines())

        Task.stop()
        new_no_tasks = len(open(DATA_FILENAME).readlines())

        self.assertEquals(no_tasks, new_no_tasks)

    def test_stop_running_task(self):
        if not os.path.exists(TASK_FILENAME):
            Task().start()
        if not os.path.exists(DATA_FILENAME):
            with open(DATA_FILENAME, mode='w') as f:
                f.write('')
        no_tasks = len(open(DATA_FILENAME).readlines())

        Task.stop()
        new_no_tasks = len(open(DATA_FILENAME).readlines())

        self.assertFalse(os.path.exists(TASK_FILENAME))
        self.assertEquals(no_tasks + 1, new_no_tasks)

    def test_start_task(self):
        if os.path.exists(TASK_FILENAME):
            os.remove(TASK_FILENAME)
        Task().start()
        self.assertTrue(os.path.exists(TASK_FILENAME))

    def test_status_task(self):
        if os.path.exists(TASK_FILENAME):
            os.remove(TASK_FILENAME)
        Task().start()
        self.assertEquals(Task.status(), True)


if __name__ == '__main__':
    unittest.main()
