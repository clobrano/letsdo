#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Setuptool configuration for letsdo
'''
import os
from setuptools import setup, find_packages

__version__ = '0.7.1'

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...


def read(fname):
    '''Read a file in current directory'''
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


def long_description():
    '''Check whether RST readme file exists to
    read it, otherwise it looks for a Markdown one'''
    if os.path.exists('README.rst'):
        return read('README.rst')
    return read('README.md')


setup(name='letsdo',
      author='Carlo Lobrano',
      author_email='c.lobrano@gmail.com',
      description='Time tracker for Command Line',
      entry_points={'console_scripts': ['lets=letsdo:main', 'letsdo=letsdo:main']},
      include_package_data=True,
      install_requires=['docopt', 'PyYaml', 'terminaltables', 'parsedatetime', 'raffaello'],
      keywords=['productivity', 'GTD', 'time tracker'],
      license="MIT",
      long_description=long_description(),
      package_dir={'': 'src'},
      packages=find_packages('src'),
      py_modules=['letsdo', 'log', 'configuration', 'timetoolkit'],
      url='https://github.com/clobrano/letsdo',
      version=__version__,
      classifiers=[
          "Development Status :: 5 - Production/Stable",
          "Topic :: Utilities", ])
