#!/usr/bin/env python
# -*- coding: utf-8 -*-
import unittest
import os
import datetime
from time import sleep
from datetime import timedelta
from letsdo.src.letsdo import Task
from letsdo.src.letsdo import Configuration
from letsdo.src.letsdo import work_on
from letsdo.src.letsdo import str2datetime
from letsdo.src.letsdo import group_task_by
from letsdo.src.letsdo import get_tasks

class TestLetsdo(unittest.TestCase):

    def setUp(self):
        test_configuration = \
'''DATA_DIRECTORY: ~/
TODO_FILE: ~/footodo.txt
TODO_START_TAG: ''
TODO_STOP_TAG: ''
'''
        self.test_conf_file = os.path.expanduser(os.path.join('~', '.letsdo'))
        self.user_conf_bak = os.path.expanduser(os.path.join('~', '.letsdo.bak'))

        if os.path.exists(self.test_conf_file):
            # Backup user configuration file
            os.rename(self.test_conf_file, self.user_conf_bak)

            # Create test configuration file
            with open(self.test_conf_file, 'w') as f:
                f.write(test_configuration)

        self.conf = Configuration()

        if os.path.exists(self.conf.data_fullpath):
            os.remove(self.conf.data_fullpath)
        if os.path.exists(self.conf.task_fullpath):
            os.remove(self.conf.task_fullpath)

    def tearDown(self):
        if os.path.exists(self.user_conf_bak):
            os.rename(self.user_conf_bak, self.test_conf_file)
        if os.path.exists(self.conf.data_fullpath):
            os.remove(self.conf.data_fullpath)
        if os.path.exists(self.conf.task_fullpath):
            os.remove(self.conf.task_fullpath)

    def test_group_task_by(self):
        t = Task('group 1', start_str='15:00').start()
        t.stop('15:05')

        t = Task('group 2', start_str='16:00').start()
        t.stop('16:01')

        t = Task('group 1', start_str='16:02').start()
        t.stop('16:03')

        real = group_task_by(get_tasks(), 'name')
        self.assertEquals(len(real), 2)
        self.assertEquals(real[0].name, 'group 1')
        self.assertEquals(real[0].work_time, timedelta(minutes=6))
        self.assertEquals(real[1].name, 'group 2')
        self.assertEquals(real[1].work_time, timedelta(minutes=1))

    def test_str2datetime(self):
        string = '2016-11-10 19:02'
        expected_datetime = datetime.datetime(2016, 11, 10, 19, 2)
        value = str2datetime(string)
        self.assertEqual(value, expected_datetime)

        string = '2016-11-10'
        now = datetime.datetime.now()
        expected_datetime = datetime.datetime(2016, 11, 10, now.hour, now.minute)
        value = str2datetime(string)
        self.assertEqual(value, expected_datetime)

        string = '11-10'
        now = datetime.datetime.now()
        expected_datetime = datetime.datetime(now.year, 11, 10, now.hour, now.minute)
        value = str2datetime(string)
        self.assertEqual(value, expected_datetime)

        string = '11-10 19:02'
        now = datetime.datetime.now()
        expected_datetime = datetime.datetime(now.year, 11, 10, 19, 2)
        value = str2datetime(string)
        self.assertEqual(value, expected_datetime)


        string = '2016/11/10 19:02'
        expected_datetime = datetime.datetime(2016, 11, 10, 19, 2)
        value = str2datetime(string)
        self.assertEqual(value, expected_datetime)

        string = '2016/11/10'
        now = datetime.datetime.now()
        expected_datetime = datetime.datetime(2016, 11, 10, now.hour, now.minute)
        value = str2datetime(string)
        self.assertEqual(value, expected_datetime)

        string = '19:02'
        today = datetime.datetime.today()
        expected_datetime = datetime.datetime(today.year, today.month, today.day, 19, 2)
        value = str2datetime(string)
        self.assertEqual(value, expected_datetime)

        string = '9:02'
        today = datetime.datetime.today()
        expected_datetime = datetime.datetime(today.year, today.month, today.day, 9, 2)
        value = str2datetime(string)
        self.assertEqual(value, expected_datetime)

        string = '19.02'
        today = datetime.datetime.today()
        expected_datetime = datetime.datetime(today.year, today.month, today.day, 19, 2)
        value = str2datetime(string)
        self.assertEqual(value, expected_datetime)

        string = '9.02'
        today = datetime.datetime.today()
        expected_datetime = datetime.datetime(today.year, today.month, today.day, 9, 2)
        value = str2datetime(string)
        self.assertEqual(value, expected_datetime)

    def test_continue_task_by_index(self):
        for i in range(3):
            t = Task('task {id}'.format(id=i))
            t.start()
            sleep(1)
            t.stop()
            sleep(1)

        work_on(task_id=2)
        t = Task.get_running()
        self.assertEqual('task 1', t.name)

    def test_get_no_context(self):
        task = Task('project without a context')
        self.assertIsNone(task.context)

    def test_get_context(self):
        task = Task('project with a @context')
        self.assertEquals(task.context, '@context')

    def test_get_no_tags(self):
        task = Task('project without tags')
        self.assertIsNone(task.tags)

    def test_get_tags(self):
        task = Task('project with +some +tags')
        self.assertEquals(task.tags, ['+some', '+tags'])

    def test_create_unnamed_task(self):
        with self.assertRaises (TypeError) as context:
            Task ()

    def test_create_named_task(self):
        task = Task('named')
        self.assertEquals(task.name, 'named')

    def test_get_non_running_task(self):
        if os.path.exists(self.conf.task_fullpath):
            os.remove(self.conf.task_fullpath)
        task = Task.get_running()
        self.assertIsNone(task)

    def test_get_running_task(self):
        if not os.path.exists(self.conf.task_fullpath):
            Task('foo task').start()
        task = Task.get_running()
        self.assertIsNotNone(task)

    def test_stop_non_running_task(self):
        if os.path.exists(self.conf.task_fullpath):
            os.remove(self.conf.task_fullpath)
        if not os.path.exists(self.conf.data_fullpath):
            with open(self.conf.data_fullpath, mode='w') as f:
                f.write('')
        no_tasks = len(open(self.conf.data_fullpath).readlines())

        Task.stop()
        new_no_tasks = len(open(self.conf.data_fullpath).readlines())

        self.assertEquals(no_tasks, new_no_tasks)

    def test_stop_running_task(self):
        if not os.path.exists(self.conf.task_fullpath):
            Task('foo task').start()
        if not os.path.exists(self.conf.data_fullpath):
            with open(self.conf.data_fullpath, mode='w') as f:
                f.write('')
        no_tasks = len(open(self.conf.data_fullpath).readlines())

        Task.stop()
        new_no_tasks = len(open(self.conf.data_fullpath).readlines())

        self.assertFalse(os.path.exists(self.conf.task_fullpath))
        self.assertEquals(no_tasks + 1, new_no_tasks)

    def test_start_task(self):
        if os.path.exists(self.conf.task_fullpath):
            os.remove(self.conf.task_fullpath)
        Task('foo task').start()
        self.assertTrue(os.path.exists(self.conf.task_fullpath))

    def test_status_task(self):
        if os.path.exists(self.conf.task_fullpath):
            os.remove(self.conf.task_fullpath)
        Task('foo task').start()
        self.assertTrue(Task.status())


if __name__ == '__main__':
    unittest.main()
