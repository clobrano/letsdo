#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vi: set ft=python :
from datetime import datetime
from src.timetoolkit import format_h_m, strfdelta, str2datetime


def test_str2datetime():
    assert datetime(2022, 4, 2, 0, 0) == str2datetime("2022-04-02 00:00")
    assert datetime(2022, 4, 2, 1, 0) == str2datetime("2022/04/02 01:00")
    assert datetime(2022, 4, 2, 0, 2) == str2datetime("2022/04/02 00:02")
    # The following is not supported, but it should
    # assert datetime(2022, 4, 2, 0, 2) == str2datetime("2022\04\02 00:02")


def test_format_h_m():
    assert "12h 03m" == format_h_m("12:03")
    assert "4h 03m" == format_h_m("4:03")


def test_strfdelta_with_number_inputtype():
    assert " 0h 01m" == strfdelta(60, inputtype="seconds")
    assert " 1h 00m" == strfdelta(3600, inputtype="seconds")
    assert "00d 00h 01m 00s" == strfdelta(
            60,
            fmt="{D:02}d {H:02}h {M:02}m {S:02}s",
            inputtype="seconds")
    assert " 1h 00m" == strfdelta(60, inputtype="minutes")
    assert "60h 00m" == strfdelta(3600, inputtype="minutes")
    assert "00d 01h 00m 00s" == strfdelta(
            60,
            fmt="{D:02}d {H:02}h {M:02}m {S:02}s",
            inputtype="minutes")
    assert "02d 12h 00m 00s" == strfdelta(
            3600,
            fmt="{D:02}d {H:02}h {M:02}m {S:02}s",
            inputtype="minutes")
