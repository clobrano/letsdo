#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from setuptools import setup, find_packages

__version__ = '0.3.3'

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(name='letsdo',
      author='Carlo Lobrano',
      author_email='c.lobrano@gmail.com',
      description='Time tracker for Command Line',
      entry_points={'console_scripts': ['letsdo=letsdo:main']},
      include_package_data=True,
      install_requires=['docopt', 'PyYaml'],
      keywords=['productivity', 'time tracker'],
      license="MIT",
      long_description = read('README.rst'),
      package_dir={'': 'src'},
      packages=find_packages('src'),
      py_modules=['letsdo'],
      url='https://github.com/clobrano/letsdo',
      version=__version__,
      classifiers=[
           "Development Status :: 4 - Beta",
           "Topic :: Utilities",
      ]
     )
