# -*- coding: utf-8 -*-
# vi: set ft=python
"""
Usage:
    lets do     <name>... [--time=<time>]
    lets see    [all|config] [--detailed|--day-by-day] [--ascii| --dot-list] [-p|--project] [<query>...]
    lets edit
    lets cancel
    lets stop   [<time>...]
    lets goto   <newtask>...
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
"""

import os
import docopt

import handlers
from app import guess_task_id_from_string, do_report
from log import RAFFAELLO
from configuration import get_configuration, get_task_file_path, CONFIG_FILE_NAME


def main():
    """main"""
    args = docopt.docopt(__doc__)

    is_ok = True
    msg = ""

    if args["autocomplete"]:
        handlers.autocomplete()

    elif args["do"]:
        is_ok, msg = handlers.start_task_handler(
            " ".join(args["<name>"]), args["--time"]
        )

    elif args["edit"]:
        is_ok, msg = handlers.edit_file_handler(get_task_file_path())
        print(msg)
        if not is_ok:
            return 1
        return 0

    elif args["config"]:
        is_ok, msg = handlers.edit_file_handler(
            os.path.join(os.path.expanduser("~"), CONFIG_FILE_NAME),
        )

    elif args["cancel"]:
        is_ok, msg = handlers.cancel_task_handler()

    elif args["stop"]:
        is_ok, msg = handlers.stop_task_handler(" ".join(args["<time>"]))

    elif args["goto"]:
        description = " ".join(args["<newtask>"])
        is_ok, msg = handlers.goto_task_handler(description)

    if args["see"]:
        if args["<query>"]:
            args["<query>"] = " ".join(args["<query>"])

        do_report(args)

    print(msg)
    if not is_ok:
        return 1
    return 0


if __name__ == "__main__":
    main()
