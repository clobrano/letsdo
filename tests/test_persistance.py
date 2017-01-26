#!/usr/bin/env python
# -*- coding: utf-8 -*-
#!/usr/bin/env python
# -*- coding: utf-8 -*-
import unittest
import os
from letsdo.src.persistance import *

class TestPersistance(unittest.TestCase):
    def setUp(self):
        test_configuration = \
'''
datapath: /tmp/
taskpath: /tmp/
'''
        self.test_conf_file = os.path.expanduser(os.path.join('~', '.letsdo'))

        if os.path.exists(self.test_conf_file):
            with open(self.test_conf_file, 'r') as f:
                self.backup = f.read()

            with open(self.test_conf_file, 'w') as f:
                f.write(test_configuration)

        self.conf = Configuration()

        if os.path.exists(self.conf.data_filename):
            os.remove(self.conf.data_filename)
        if os.path.exists(self.conf.task_filename):
            os.remove(self.conf.task_filename)

    def tearDown(self):
        if os.path.exists(self.test_conf_file):
            with open(self.test_conf_file, 'w') as f:
                f.write(self.backup)
        if os.path.exists(self.conf.data_filename):
            os.remove(self.conf.data_filename)
        if os.path.exists(self.conf.task_filename):
            os.remove(self.conf.task_filename)

    def testConfiguration(self):
        home = os.path.expanduser('~')
        self.assertEquals(Configuration().task_filename, os.path.join('/', 'tmp', '.letsdo-task'))
        self.assertEquals(Configuration().data_filename, os.path.join('/', 'tmp', '.letsdo-data'))

    def testSaveTask(self):
        rv = save_json_task({'name': 'task'})
        self.assertTrue(rv)
        self.assertTrue(os.path.exists(Configuration().task_filename), "Task file not created")

    def testLoadTask(self):
        rv = save_json_task(None)
        self.assertTrue(rv)

