[![PyPI version](https://badge.fury.io/py/letsdo.svg)](https://badge.fury.io/py/letsdo)
# Letsdo, the CLI time tracker

Letsdo helps you to be more productive and focused, tracking the time you spend on various tasks:

    $ letsdo start letsdo-readme
      Starting task 'letsdo-readme' now

Letsdo shows you the name of the current running tasks and the time you've already spent on it:

    $ letsdo status
      Working on 'letsdo-readme' for 0:10:58

If you have made any mistake with the task name or just want to modify it, use 'rename':

    $ letsdo rename "letsdo the greatest readme"
      Renaming task 'letsdo-readme' to 'letsdo the greatest readme'

Once the task is completed, just 'stop' it:

    $ letsdo stop
      Stopped task 'letsdo the greatest readme' after 0:18:27

Moreover Letsdo shows you a full report of all your tasks grouped by day, summing up the time spent on each task

    $ letsdo report

    ===================================
    2016-11-04| Total time: 2:25:24
    -----------------------------------
    2016-11-04| 0:18:27 - letsdo the greatest readme
    2016-11-04| 0:50:00 - test-qc-driver-cradlepoint
    2016-11-04| 0:03:32 - letsdo-move-to-another-task
    2016-11-04| 0:01:17 - unknown
    2016-11-04| 0:11:45 - letsdo rename
    2016-11-04| 0:11:50 - letsdo-save
    2016-11-04| 0:03:49 - fix-rename-command
    2016-11-04| 0:06:41 - working-hours
    2016-11-04| 0:14:08 - letsdo-readme
    2016-11-04| 0:14:30 - letsdo-tidying-up
    2016-11-04| 0:05:09 - letsdo-save-new-feature
    2016-11-04| 0:13:27 - letsdo-setup.py
    2016-11-04| 0:00:49 - letsdo-test-new-feature

    ===================================
    2016-11-03| Total time: 1:50:14
    -----------------------------------
    2016-11-03| 0:17:21 - working_hours
    2016-11-03| 0:56:18 - setup-env
    2016-11-03| 0:07:08 - unknow
    2016-11-03| 0:29:13 - pynicom-fix-commands
    2016-11-03| 0:00:14 - unknown

The Report comes from a plain text file under $HOME/.letsdo-report.
In the coming version the path to this file will be configurable to make it easier to syncronize it among several systems (e.g. with Dropbox).

Letsdo does not really need a task name to start, so you can start tracking your work and choose a name for it later.

    $ letsdo start
      Starting task 'unknown' now


