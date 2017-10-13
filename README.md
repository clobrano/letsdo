[![Snap Status](https://build.snapcraft.io/badge/clobrano/letsdo.svg)](https://build.snapcraft.io/user/clobrano/letsdo)
[![PyPI version](https://badge.fury.io/py/letsdo.svg)](https://badge.fury.io/py/letsdo)
[![Build Status](https://travis-ci.org/clobrano/letsdo.svg?branch=master)](https://travis-ci.org/clobrano/letsdo)
# Letsdo, the CLI time-tracker

Letsdo helps you to be more focused and productive, tracking your TODO and the time you spend working on them.

# Features

Have a look at the **help** message:

```
$ letsdo
Usage:
    lets see    [todo|all|today|yesterday] [--detailed|--day-by-day] [--ascii] [<pattern>] [--no-color]
    lets do     [--time=<time>] [<name>...] [--no-color]
    lets stop   [--time=<time>] [--no-color]
    lets goto   [<newtask>...] [--no-color]
    lets cancel [--no-color]
    lets edit
    lets config data.directory <fullpath>
    lets config todo.file      <fullpath>
    lets config todo.start     <tag>
    lets config todo.stop      <tag>
    lets config autocomplete
```

First of all, we do not want to waste time typing too much. **Letsdo is the name of the package** and you can use it as well **as command line interface**, but all the interface is designed to be as informal as possible, so **you are encouraged to use lets instead**. Said that, when you do not know what to do, just write **lets see**, this command shows the current status of your task, whether you're doing something or not

```
$ lets see
```

When you're ready to start with something just type **lets do** followed by a short description. **Contexts**, and **Projects** are supported in form of words starting with **@** sign, or **+** sign respectively. With this configuration there isn't much difference between contexts and projects and other words, but if you're keen to install another package named **Raffaello**, we can then enable **colors**

```
$ pip install raffaello
$ export LETSDO_COLOR=1
$ lets see
```

You can **edit** the current task's name or starting time, **cancel** it or **stop** it. Once stopped, the task is saved in your **history**, that by default is located under your HOME directory in a file called 'letsdo-data'.

Don't you like the default location, let's have a look at the **config** sub-command:

- **data.directory** is the preferred location for both history and current task's data. You can share your work using a file sharing service.

e.g.

```
$ lets config data.directory ~/Dropbox
```

Let's see now the history: you can rapidly have a look at **today** and **yesterday** work done by typing:

```
$ lets see today
$ lets see yesterday
```

If you want to see the work done in another date, just write the date:

```
lets see 2017-07-13
```

a partial date will do as well, just keep the same order: Year first, then Month and Day

```
lets see 17-07-13
```

you can even use only '07-13' if you have not yet tracked data in different years.

The same way, you can look at all the work done in a particular month:

e.g in July 2017

```
lets see 17-07
```

or **all** your tasks:

```
lets see all
```

or again, a specific project or all the tasks that share a pattern:

```
lets see +letsdo
```

As you can see, tasks are reported along with an ID. That's because I'm not happy with typing too much.
To start again an older task, use the ID:

```
lets do 10
```

or if you just one to start again the **last** task you stopped

```
lets do last
```

Do you switch often among tasks? Do not need to stop and start again, just **goto** using description or ID again:

```
lets goto new project
lets goto 3
```

Finally, you can configure **autocompletion** to let Letsdo suggest your flags, contexts and projects' names, type **lets config autocomplete** and follow the instructions.

# Advanced usage

Well, not that advanced. Everybody has a todo list, so letsdo can read it

```
lets config todo.file ~/todo.txt
lets see todo
```

If you have different stuff in your todo.txt file, just provide an header to the list and configure letsdo to look for it

```
lets config todo.start todos
lets see todo
```

if you don't provide a todo.stop, Letsdo will stop reading at the first blank line.

# Licence
Letsdo is release under the [MIT](https://opensource.org/licenses/MIT) license. See LICENSE file for more details.


# Contributions
I am really happy to consider any PR that can make Letsdo better.
