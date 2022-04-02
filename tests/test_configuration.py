#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vi: set ft=python :
from os import remove
from os.path import join, exists, dirname, abspath
import pytest
import yaml
import src.configuration as configuration

DUMMYCONFIGURATION_FILENAME = ".letsdo"
DUMMYCONFIGURATION_FULLPATH = join(
        dirname(__file__),
        DUMMYCONFIGURATION_FILENAME)


@pytest.fixture
def create_configuration_date():
    dummyconfiguraion = {
            "COLOR_ENABLED": True,
            "DATA_DIRECTORY": dirname(__file__)}

    with open(DUMMYCONFIGURATION_FULLPATH, "w") as f:
        yaml.dump(dummyconfiguraion, f, default_flow_style=False)
    yield

    # teardown
    if exists(DUMMYCONFIGURATION_FULLPATH):
        remove(DUMMYCONFIGURATION_FULLPATH)


def testConfigurationFileExists(create_configuration_date):
    assert exists(
        DUMMYCONFIGURATION_FULLPATH
    ), f"could not find {DUMMYCONFIGURATION_FULLPATH}"


def testConfigurationLoad(create_configuration_date):
    data = configuration.load(home=dirname(__file__))
    fullpath = abspath(dirname(__file__))
    assert data["COLOR_ENABLED"], f'color enabled is {data["COLOR_ENABLED"]}'
    assert (
        data["DATA_DIRECTORY"] == fullpath
    ), f'data directory is {data["DATA_DIRECTORY"]}'


def testConfigurationSave(create_configuration_date):
    data = configuration.load(dirname(__file__))
    data["COLOR_ENABLED"] = False
    configuration.save(data, home=dirname(__file__))
    data = configuration.load(dirname(__file__))
    assert not data["COLOR_ENABLED"],\
        f'color enabled is {data["COLOR_ENABLED"]}'
