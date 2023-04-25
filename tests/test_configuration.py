# -*- coding: utf-8 -*-
# vi: set ft=python :
"""Unittest for configuration module"""
import os
import unittest
import tempfile
from configuration import (
    create_default_configuration,
    get_configuration,
    get_task_file_path,
)


class TestConfiguration(unittest.TestCase):
    """Test for configuration modules"""

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()

    def test_default_configuration(self):
        """Test default configuration creation"""
        self.assertTrue(os.path.exists(self.test_dir.name))
        create_default_configuration(self.test_dir.name)
        self.assertIsNotNone(get_configuration(self.test_dir.name))
        self.assertEqual(
            get_configuration(self.test_dir.name)["data_directory"], self.test_dir.name
        )

    def test_task_file_path(self):
        """Test task file path value"""
        create_default_configuration(self.test_dir.name)
        self.assertEqual(
            get_task_file_path(self.test_dir.name),
            os.path.join(self.test_dir.name, "letsdo-task"),
        )
