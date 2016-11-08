#!/usr/bin/env python
# -*- coding: utf-8 -*-
import unittest
import os
from letsdo.src.letsdo import Task
from letsdo.src.letsdo import Configuration

class TestLetsdo(unittest.TestCase):

    def setUp(self):
        self.conf = Configuration()

    def test_create_unnamed_task(self):
        task = Task()
        self.assertEquals(task.name, 'unknown')

    def test_create_named_task(self):
        task = Task('named')
        self.assertEquals(task.name, 'named')

    def test_get_non_running_task(self):
        if os.path.exists(self.conf.task_filename):
            os.remove(self.conf.task_filename)
        task = Task.get()
        self.assertEquals(task, None)

    def test_get_running_task(self):
        if not os.path.exists(self.conf.task_filename):
            Task().start()
        task = Task.get()
        self.assertNotEquals(task, None)

    def test_change_non_running_task(self):
        if os.path.exists(self.conf.task_filename):
            os.remove(self.conf.task_filename)
        ret = Task.change('newname')
        self.assertEqual(ret, None)

    def test_change_running_task(self):
        if not os.path.exists(self.conf.task_filename):
            Task().start()
        Task.change('newname')
        self.assertEqual(Task.get().name, 'newname')

    def test_stop_non_running_task(self):
        if os.path.exists(self.conf.task_filename):
            os.remove(self.conf.task_filename)
        if not os.path.exists(self.conf.data_filename):
            with open(self.conf.data_filename, mode='w') as f:
                f.write('')
        no_tasks = len(open(self.conf.data_filename).readlines())

        Task.stop()
        new_no_tasks = len(open(self.conf.data_filename).readlines())

        self.assertEquals(no_tasks, new_no_tasks)

    def test_stop_running_task(self):
        if not os.path.exists(self.conf.task_filename):
            Task().start()
        if not os.path.exists(self.conf.data_filename):
            with open(self.conf.data_filename, mode='w') as f:
                f.write('')
        no_tasks = len(open(self.conf.data_filename).readlines())

        Task.stop()
        new_no_tasks = len(open(self.conf.data_filename).readlines())

        self.assertFalse(os.path.exists(self.conf.task_filename))
        self.assertEquals(no_tasks + 1, new_no_tasks)

    def test_start_task(self):
        if os.path.exists(self.conf.task_filename):
            os.remove(self.conf.task_filename)
        Task().start()
        self.assertTrue(os.path.exists(self.conf.task_filename))

    def test_status_task(self):
        if os.path.exists(self.conf.task_filename):
            os.remove(self.conf.task_filename)
        Task().start()
        self.assertEquals(Task.status(), True)


if __name__ == '__main__':
    unittest.main()
