#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Setuptool configuration for letsdo
"""
from setuptools import setup, find_packages

__version__ = "0.7.2"

with open("README.md", "r", encoding="UTF-8") as f:
    long_description = f.read()

setup(
    name="letsdo",
    version=__version__,
    description="Time tracker for Command Line",
    package_dir={"": "src"},
    packages=find_packages("src"),
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/clobrano/letsdo",
    author="Carlo Lobrano",
    author_email="c.lobrano@gmail.com",
    license="GPL3",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Topic :: Utilities",
    ],
    install_requires=[
        "docopt",
        "PyYaml",
        "terminaltables",
        "parsedatetime",
        "raffaello",
    ],
    extras_require={
        "dev": ["pytest>=7.0", "twine>=4.0.2"],
    },
    entry_points={"console_scripts": ["lets=letsdo:main", "letsdo=letsdo:main"]},
    include_package_data=True,
    keywords=["productivity", "GTD", "time tracker"],
    py_modules=["letsdo", "log", "configuration", "timetoolkit"],
)
