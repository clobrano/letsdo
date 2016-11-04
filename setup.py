#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

__version__ = '0.1.0'

setup(name='letsdo',
      author='Carlo Lobrano',
      author_email='c.lobrano@gmail.com',
      description='Time tracker for Command Line',
      entry_points={'console_scripts': ['letsdo=letsdo:main']},
      include_package_data=True,
      install_requires=['docopt', ],
      keywords=['productivity', 'time tracker'],
      license="MIT",
      #long_description = read('README.md'),
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
