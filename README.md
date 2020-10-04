[![Snap Status](https://build.snapcraft.io/badge/clobrano/letsdo.svg)](https://build.snapcraft.io/user/clobrano/letsdo)
[![PyPI version](https://badge.fury.io/py/letsdo.svg)](https://badge.fury.io/py/letsdo)
[![Build Status](https://travis-ci.org/clobrano/letsdo.svg?branch=master)](https://travis-ci.org/clobrano/letsdo)
# Letsdo, the CLI time-tracker

Letsdo helps you to be more focused and productive tracking the time you spend on your work activities.

# Features

Have a look at the **help** message:

```
$ letsdo
Usage:
    lets do     <name>... [--time=<time>]
    lets see    [all|config] [--detailed|--day-by-day] [--ascii| --dot-list] [-p|--project] [<query>...]
    lets edit
    lets cancel
    lets stop   [<time>...]
    lets goto   <newtask>...
    lets track  <name>...
    lets config
    lets autocomplete

options:
    -a, --ascii       Print report table in ASCII characters
    -t, --time=<time> Change the start/stop time of the task on the fly

examples:
    lets see            # show today's activities
    lets see yesterday  # show yesterday's activities
    lets see 2018-07    # show 2018 July's activities
    lets see last July  # same as above (if we're still in 2019)
    lets see +project   # show activities with +project tag (+project is autocompleted with TAB)
    lets see something  # show activities whose description has he word 'something'
    lets see this week
    lets see last month
    lets see 2019
    ...

```

First of all, we do not want to waste time typing too much. **Letsdo is the name of the package** and you can use it as well **as command line interface**, but all the interface is designed to be as informal as possible, so you are encouraged to use **lets** instead.

That said, when you do not know what to do, just write **lets see**, this command shows the current status of your task, whether you're doing something or not

```
$ lets see
```

When you're ready to start with something just type **lets do** followed by a short description.

~~~sh
$ lets do write a good readme
task 'write a good readme' started at 2020-10-04 11:38:00
~~~

**Contexts**, and **Projects** are supported in form of words starting with **@**, or **+** signs respectively.

~~~sh
$ lets do +myproject write a good readme
task '+myproject write a good readme' started at 2020-10-04 11:38:00
~~~

You can **edit** the current task's name or starting time, **cancel** it or **stop** it.

~~~sh
$ lets stop
stopped task '+myproject write a good readme @github' after 0 hours, 40 minutes
~~~

~~~sh
$ lets do foo
task 'foo' started at 2020-10-04 12:30:00
$ lets cancel
Cancelled task
{
    "name": "foo",
    "start": "2020-10-04 12:30:58.404926"
}
~~~

If you forgot to stop the task on time, you can adjust it giving an absolute or relative time:

~~~sh
$ lets stop 11:02
$ lets stop 10 minutes ago
~~~

Once stopped, the task is saved in your **history**, that by default is located under your `HOME` directory in a file called 'letsdo-data'.

Don't you like the default location? let's have a look at the **config** sub-command:

~~~sh
$ lets config
~~~

**config** opens the configuration file (HOME/.letsdo) with two configurable fields

```
COLOR_ENABLED: true
DATA_DIRECTORY: /home/carlo
```

Let's see now the history: you can rapidly have a look at **today** and **yesterday** work done by typing:

```
$ lets see today
$ lets see yesterday
```

If you want to see the work done in another date, just write the date:

```
$ lets see 2017-07-13
```

a partial date will do as well, just keep the same order: Year first, then Month and Day

```
$ lets see 17-07-13
```

you can even use only '07-13' if you have not yet tracked data in different years.

The same way, you can look at all the work done in a particular month:

e.g in July 2017

```
$ lets see 17-07
```

or **all** your tasks:

```
$ lets see all
```

or again, a specific project or all the tasks that share a pattern:

```
$ lets see +myproject
```

As you can see, tasks are reported along with an ID, so you can re-start the same task again using its ID:

```
$ lets do 10
```

or if you just want to start again the **last** task you stopped

```
$ lets do last
```

Do you switch often among tasks? Do not need to stop and start again, just **goto** using description or ID again:

```
$ lets goto new project
$ lets goto 3
```

Finally, you can configure **autocompletion** to let Letsdo suggest your flags, contexts and projects' names, type **lets config autocomplete** and follow the instructions.

# Licence
Letsdo is release under the [MIT](https://opensource.org/licenses/MIT) license. See LICENSE file for more details.


# Contributions
I am really happy to consider any PR that can make Letsdo better.
