#!/usr/bin/env python
# -*- coding: utf-8 -*-
import unittest
import os
from letsdo.src.letsdo import Task
from letsdo.src.letsdo import Configuration

class TestLetsdo(unittest.TestCase):

    def setUp(self):
        self.conf = Configuration()
        if os.path.exists(self.conf.data_filename):
            os.remove(self.conf.data_filename)
        if os.path.exists(self.conf.task_filename):
            os.remove(self.conf.task_filename)

    def test_save_context(self):
        task = Task('test save @context')
        task.start()
        task.stop()
        last_saved_task = open(self.conf.data_filename).readlines()[-1].strip()
        self.assertTrue('test save @context' in last_saved_task)
        context = last_saved_task.split(',')[5]
        self.assertEqual('@context', context)

    def test_save_no_context(self):
        task = Task('test save no context')
        task.start()
        task.stop()
        last_saved_task = open(self.conf.data_filename).readlines()[-1].strip()
        context = last_saved_task.split(',')[5]
        self.assertEqual(context, 'None')

    def test_save_tags(self):
        task = Task('test save +tagA +tagB mixed with +text')
        task.start()
        task.stop()
        last_saved_task = open(self.conf.data_filename).readlines()[-1].strip()
        tags = last_saved_task.split(',')[6]
        self.assertEqual('+tagA +tagB +text', tags)

    def test_save_no_tag(self):
        task = Task('test save no tag')
        task.start()
        task.stop()
        last_saved_task = open(self.conf.data_filename).readlines()[-1].strip()
        tags = last_saved_task.split(',')[6]
        self.assertEqual('None', tags)

    def test_get_no_context(self):
        task = Task('project without a context')
        self.assertEquals(task.context, None)

    def test_get_context(self):
        task = Task('project with a @context')
        self.assertEquals(task.context, '@context')

    def test_get_no_tags(self):
        task = Task('project without tags')
        self.assertEquals(task.tags, None)

    def test_get_tags(self):
        task = Task('project with +some +tags')
        self.assertEquals(task.tags, ['+some', '+tags'])

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
