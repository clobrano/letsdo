[![PyPI version](https://badge.fury.io/py/letsdo.svg)](https://badge.fury.io/py/letsdo)
[![Build Status](https://travis-ci.org/clobrano/letsdo.svg?branch=master)](https://travis-ci.org/clobrano/letsdo)
# Letsdo, the CLI time tracker

Letsdo helps you to be more productive and focused, tracking the time you spend on various tasks:

    $ letsdo letsdo-readme
      Starting task 'letsdo-readme'

You can pass whatever string to Letsdo in order to describe your task

    $ letsdo best readme in the istory of github
      Starting task 'best readme in the istory of github'

and change its description if you like

    $ letsdo --change best readme in the history of github
      Renaming task 'best readme in the istory of github' to 'best readme in the History of github'

but if you just made a little typo, might be better to use --replace and --with flags:

    $ letsdo --replace github --with GitHub

    $ letsdo --change best readme in the history of github
      Renaming task 'best readme in the History of github' to 'best readme in the History of GitHub'

When a task is running, executing Letsdo will prompt the time spent on it

    $ letsdo
      Working on 'best readme in the History of GitHub' for 0:01:32

Once the task is completed, just 'stop' it:

    $ letsdo --stop
      Stopped task 'best readme in the History of GitHub' after 0:01:45

Let's say you do not want to stop, but just move to another task, use --to flag

    $ letsdo previous task
      Starting task 'previous task'
    $ letsdo --to  new task
      Stopped task 'previous task' after 0:00:08
      Starting task 'new task'

Now stop, and see some reports

    $ letsdo --stop
      Stopped task 'new task' after 0:00:25

Total time for each task (tasks with the same name are considered as one)

    $ letsdo --report
      [0] 2016-11-14| 0:00:00 - letsdo-readme
      [1] 2016-11-14| 0:01:00 - best readme in the History of GitHub
      [2] 2016-11-14| 0:01:00 - previous task
      [3] 2016-11-14| 0:00:00 - new task

See all the tasks' start and stop time, day by day (time is in 24h format)

    $ letsdo --report --full
    ===================================
    2016-11-14| Total time: 0:02:00
    -----------------------------------
    2016-11-14| 0:00:00 (16:03 -> 16:03) - letsdo-readme
    2016-11-14| 0:01:00 (16:04 -> 16:05) - best readme in the History of GitHub
    2016-11-14| 0:01:00 (16:06 -> 16:07) - previous task
    2016-11-14| 0:00:00 (16:07 -> 16:07) - new task

See total time per task and per day

    $ letsdo --report --daily
    ===================================
    2016-11-14| Total time: 0:02:00
    -----------------------------------
    2016-11-14| 0:00:00 - letsdo-readme
    2016-11-14| 0:01:00 - best readme in the History of GitHub
    2016-11-14| 0:01:00 - previous task
    2016-11-14| 0:00:00 - new task

Now, back working again on a previous task, too bad the name is too long to type it! No problem, just use --keep flag to
keep working on the last task

    $ letsdo --keep
      Starting task 'new task'

But, I do not want to work on the last! Then use the --id flag (the task index is the one reported with --report flag)

    $ letsdo --stop
      Stopped task 'new task' after 0:00:50
    $ letsdo --keep --id 1
      Starting task 'best readme in the History of GitHub'

Clearly, all the flags support the short version (-k for --keep, -i for --id, etc.)

The Report comes from a plain text file under <letsdopath>/.letsdo-data

The <letsdopath> comes from Letsdo configuration file, stored in your $HOME directory:

    $ cat ~/.letsdo
    letsdopath: ~/Dropbox/

To have a configuration file is not necessary since Letsdo uses the $HOME as default folder to store its data.
However, setting a datapath is useful in order to share tasks on multiple devices (with Dropbox for example)

Finally, if you forgot to start/stop a task at the right moment, just use the --time flag followed by the HOUR:MINUTE
string of the correct moment if in the same day or "DATE HOUR:MINUTE".

e.g.

    $ letsdo -s -t "2016-10-12 12:00"

This command stops the running tasks storing the "stop time" at the given date. Letsdo will guess
some data if not provided, as example `letsdo -s -t "02-04 12:00` will stop the running task
assuming the date being the 4th of Febbruary of the **current** year.


## @Contexts, +tags and autocompletion

One can specify the task with @contexts (only one per tasks) and +tags (no limits) and Letsdo bash completion is smart
enough to autocomplete also @contexts and @tags. Use --autocomplete flag for more information
