#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import yaml
import logging
import json

# Logger
level = logging.INFO
logging.basicConfig(level=level, format='  %(message)s')
logger = logging.getLogger(__name__)
info = lambda x: logger.info(x)
err = lambda x: logger.error(x)
warn = lambda x: logger.warn(x)
dbg = lambda x: logger.debug(x)


class Configuration(object):

    def __init__(self):
        conf_file_path = os.path.expanduser(os.path.join('~', '.letsdo'))
        if os.path.exists(conf_file_path):
            configuration = yaml.load(open(conf_file_path).read())
            self.data_filename = os.path.expanduser(os.path.join(configuration['datapath'], '.letsdo-data'))
            self.task_filename = os.path.expanduser(os.path.join(configuration['taskpath'], '.letsdo-task'))
            dbg('Configuration: data filename {file}'.format(file = self.data_filename))
            dbg('Configuration: task filename {file}'.format(file = self.task_filename))
        else:
            dbg('Config file not found. Using default')
            self.data_filename = os.path.expanduser(os.path.join('~', '.letsdo-data'))
            self.task_filename = os.path.expanduser(os.path.join('~', '.letsdo-task'))



def save_json_task(json_task):
    '''Save running task'''
    task_file = Configuration().task_filename
    with open(task_file, 'w') as f:
        json.dump(json_task, f)
    return True


def load_json_task():
    '''Load running task'''
    task_file = Configuration().task_filename
    if os.path.exists(task_file):
        with open(task_file, 'r') as f:
            return json.load(f)
    return True


def load_all_tasks():
    '''Load all stored tasks'''
    pass
