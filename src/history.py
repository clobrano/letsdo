#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vi: set ft=python :
"""
History module access the Tasks object from the storage
"""

from pathlib import Path
from abc import ABC, abstractmethod
from datetime import datetime

from dateparser.search import search_dates

import pandas as pd

from configuration import get_history_file_path
from tasks import Task


class History(ABC):
    @abstractmethod
    def get_tasks_by_query(self, condition: str = None) -> list[Task]:
        """Get all tasks by condition"""


class CSVHistory:
    def get_tasks_by_query(
        self,
        query: str,
    ) -> list[Task]:
        dataFrame = pd.read_csv(Path(get_history_file_path()))

        # convert start and stop column to datetime dropping hours and minutes
        dataFrame["start"] = pd.to_datetime(dataFrame["start"]).dt.date
        dataFrame["stop"] = pd.to_datetime(dataFrame["stop"]).dt.date

        if query:
            dates = parse_dates_from_query(query)
            if not dates:
                dataFrame = dataFrame[dataFrame["description"].str.contains(query)]
            elif len(dates) > 1:
                dataFrame = filter_dataframe_via_date(dataFrame, dates[0], dates[1])
            else:
                dataFrame = get_dataframe_row_via_date(dataFrame, dates[0])

        return [
            Task(
                uid=row["uid"],
                start=row["start"],
                stop=row["stop"],
                description=row["description"],
            )
            for index, row in dataFrame.iterrows()
        ]


def get_dataframe_row_via_date(dataFrame: pd.DataFrame, date: str):
    """Get a row from a data frame via date"""
    row = dataFrame.loc[dataFrame["stop"] == date]
    return row


def filter_dataframe_via_date(dataFrame: pd.DataFrame, start_date: str, stop_date: str):
    """Filter a data frame via date"""
    filtered_dataFrame = dataFrame.loc[
        (dataFrame["stop"] >= start_date) & (dataFrame["stop"] <= stop_date)
    ]
    return filtered_dataFrame


def infer_query_is_date_range(query: str):
    """Infer if the query is a date range"""
    dates = search_dates(query)
    if not dates or len(dates) != 2:
        return False
    return True


def infer_query_has_date(query: str):
    """Infer if the query has a date"""
    return search_dates(query) is not None


def parse_dates_from_query(query: str) -> list[datetime.date]:
    """Parse dates from a query with dateparser"""
    dates = search_dates(query)
    if not dates:
        return []
    # get only the date part as list
    return [date[1].date() for date in dates]
