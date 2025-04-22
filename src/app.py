import os
import re
from datetime import datetime, timedelta
from terminaltables import SingleTable, AsciiTable
from tasks import Task
from log import LOGGER, RAFFAELLO
from configuration import get_configuration, get_history_file_path
from timetoolkit import str2datetime, strfdelta


def _p(msg):
    """Colorize message"""
    if msg and get_configuration()["color"] and RAFFAELLO:
        return RAFFAELLO.paint(str(msg))
    return msg


FORMAT = "%Y-%m-%d %H:%M"


def store_task(task: Task):
    """
    Store the Task in history
    """
    with open(get_history_file_path(), "a", encoding="utf-8") as file:
        row = f"{task.uid},{task.start.strftime(FORMAT)},{task.stop.strftime(FORMAT)},{strfdelta(task.work)},{task.description}\n"
        file.write(row)


def work_on(task_id=0, start_time_str=None):
    """Start given task id"""
    tasks = get_tasks(condition=lambda x: x.tid == task_id)
    tasks = group_task_by(tasks, group="name")
    if not tasks:
        LOGGER.error("could not find task ID '%s'", task_id)
    else:
        task = tasks[0]
        start_time = None
        if start_time_str:
            date_str = datetime.strftime(datetime.today(), "%Y-%m-%d")
            start_time = date_str + " " + start_time_str

        Task(task.name, start_str=start_time).start()


def sanitize(text):
    """Remove symbols, dates and Markdown syntax from text"""
    # remove initial list symbol (if any)
    if re.match(r"^[\-\*]", text):
        text = re.sub(r"^[\-\*]", "", text)

    # remove initial date (yyyy-mm-dd)
    if re.match(r"^\s*\d+-\d+-\d+\s+", text):
        text = re.sub(r"^\s*\d+-\d+-\d+\s+", "", text)

    # remove initial date (yy\date-of-year)
    if re.match(r"^\s*\d+/\d+\s+", text):
        text = re.sub(r"^\s*\d+/\d+\s+", "", text)

    # remove markdown links
    md_link = re.compile(r"\[(.*)\]\(.*\)")
    has_link = md_link.search(text)
    if has_link:
        link_name = md_link.findall(text)
        text = re.sub(r"\[(.*)\]\(.*\)", link_name[0], text)

    return text


def get_tasks(condition=None):
    """Get all tasks by condition"""
    tasks = []

    tid = 0
    uids = dict()
    try:
        history_file_path = get_history_file_path()
        if not os.path.exists(history_file_path):
            LOGGER.info("No Task recorded yet")
            return []

        with open(get_history_file_path()) as cfile:
            for line in reversed(cfile.readlines()):
                fields = line.strip().split(",")
                if not fields[1]:
                    continue

                # Take care of old history format with worked_time
                if len(fields) == 5:
                    task = Task(
                        name=sanitize(fields[1]), start_str=fields[3], end_str=fields[4]
                    )
                elif len(fields) == 4:
                    task = Task(
                        name=sanitize(fields[1]), start_str=fields[2], end_str=fields[3]
                    )
                else:
                    raise Exception(
                        "History unexpected fields ({}: {})".format(len(fields), fields)
                    )

                # Tasks with same UID share the same Task ID as well
                # Integer IDs are easier to use than hash IDs
                if task.uid not in uids:
                    tid += 1
                    uids[task.uid] = tid
                task.tid = uids[task.uid]
                tasks.append(task)

        conditioned = filter(condition, tasks)
        return list(conditioned)
    except IOError as error:
        LOGGER.error("could not get tasks' history: %s", error)
        return []


def group_task_by(tasks, group=None):
    """Group given task by name or date"""
    if group == "name":
        uniques = []
        for task in tasks:
            if task not in uniques:
                uniques.append(task)

        for main_task in uniques:
            work_time_in_seconds = sum(
                [
                    same_task.work_time.seconds
                    for same_task in tasks
                    if same_task == main_task
                ]
            )
            work_time = timedelta(seconds=work_time_in_seconds)
            main_task.work_time = work_time
        return uniques

    if group == "date":
        task_map = {}
        for task in tasks:
            date = task.last_end_date
            if date in task_map.keys():
                task_map[date].append(task)
            else:
                task_map[date] = [task]
        return task_map

    LOGGER.warning("Could not group tasks by: %s", group)
    return tasks


def report_task(tasks, title=None, detailed=False, ascii=False):
    """Display table with tasks data"""

    table_data = [["ID", "Last update", "Work time", "Description"]]
    if detailed:
        table_data = [["ID", "Last update", "Work time", "Interval", "Description"]]
        tasks = sorted(tasks, key=lambda x: x.end_time, reverse=True)

    tot_work_time = timedelta()
    for task in tasks:
        tot_work_time += task.work_time

    for task in tasks:
        last_time = ""
        if task.last_end_date:
            if task.tid != "R":
                last_time = task.end_time.strftime("%d-%m-%Y w%V")
            else:
                last_time = task.start_time.strftime("%Y-%m-%d %H:%M")

        perc = 0
        if tot_work_time > timedelta(0):
            perc = int((task.work_time / tot_work_time) * 100)

        time = "{} {:2d}%".format(strfdelta(task.work_time, fmt="{H:2}h {M:02}m"), perc)

        # smart break message at boundaries
        task_name = task.name
        if len(task.name) > 53:
            word_break = task_name.find(" ", 45)
            if word_break == -1:
                word_break = 45
            task_name = task_name[:word_break] + "\n ⤷" + task_name[word_break:]

        if detailed:
            begin = task.start_time.strftime("%H:%M")
            end = task.end_time.strftime("%H:%M")
            interval = "{} -> {}".format(begin, end)

            row = [_p(task.tid), _p(last_time), _p(time), _p(interval), _p(task_name)]
        else:
            row = [_p(task.tid), _p(last_time), _p(time), _p(task_name)]

        table_data.append(row)

    if len(tasks) == 0:
        print(_p("Nothing to show for %s" % title))
        return

    if title:
        title = " %s " % title

    if len(tasks) > 1:
        recap = "activities,"
    else:
        recap = "activity,"
    table_data.append(
        [
            len(tasks),
            recap,
            "total time:",
            _p(strfdelta(tot_work_time, fmt="{H:2}h {M:02}m")),
        ]
    )

    if ascii:
        table = AsciiTable(table_data, title)
    else:
        table = SingleTable(table_data, title)

    table.outer_border = True
    table.inner_column_border = False
    table.inner_heading_row_border = True
    table.inner_footing_row_border = True
    table.justify_columns[0] = "right"
    table.justify_columns[1] = "center"
    table.justify_columns[2] = "right"
    table.justify_columns[3] = "left"

    print("")
    print(table.table)


def __is_a_month(string):
    months = [
        "jan",
        "feb",
        "mar",
        "apr",
        "may",
        "jun",
        "jul",
        "aug",
        "sep",
        "oct",
        "nov",
        "dec",
    ]
    if string.lower() in months:
        return True

    for month in months:
        if month in string.lower():
            return True

    return False


def __get_time_format_from_query(query):
    format = "%Y-%m-%d"

    if not query:
        return format

    if "last year" in query:
        format = "%Y"
    elif "week" in query:
        format = "%V"
        week_check = True
    elif "month" in query or __is_a_month(query):
        format = "%Y-%m"

    return format


def __get_task_condition_from_query(query):
    format = __get_time_format_from_query(query)
    try:
        query = datetime.strftime(str2datetime(query), format)
    except:
        LOGGER.debug("query '%s' does not seems a date", query)

    if format == "%V":
        condition = lambda x: x.week_no == query and x.end_time.strftime(
            "%Y"
        ) == datetime.now().strftime("%Y")
    else:
        condition = lambda x: not query or (
            query in str(x.last_end_date) or query in x.name
        )

    return condition, query, format


def do_report(args):
    """Wrap show reports"""

    if not args["all"] and not args["<query>"]:
        args["<query>"] = "today"

    query = args["<query>"]

    condition, date, format = __get_task_condition_from_query(query)

    if format == "%V":
        title = "week {}".format(date)
    else:
        title = "{}".format(date)

    tasks = get_tasks(condition)

    if args["--detailed"]:
        tasks.reverse()
        report_task(tasks, title=title, detailed=True, ascii=args["--ascii"])
        return

    if args["--day-by-day"]:
        task_map = group_task_by(tasks, "date")

        for key in sorted(task_map.keys()):
            if not key:
                continue

            task = group_task_by(task_map[key], "name")
            sorted_by_time = sorted(task, key=lambda x: x.work_time, reverse=True)

            report_task(sorted_by_time)
        return

    tasks = group_task_by(tasks, "name")
    if args["--dot-list"]:
        print(_p("\n{}".format(title)))

        for task in tasks:
            print(_p(" ● (%s) %s" % (task.tid, task.name)))
        return

    running = Task.get_running()
    current_running = ["today", "now", "this week", "this month"]
    if running and (
        not query or query.lower() in current_running or query in running.name
    ):
        running.tid = "R"
        running.work_time = datetime.now() - running.start_time
        running.end_time = running.start_time
        tasks.insert(0, running)

    report_task(tasks, title=title, detailed=args["--detailed"], ascii=args["--ascii"])


def guess_task_id_from_string(task_name: str) -> (int, bool):
    """
    Get task ID from task name

    Support for "task_name" being only the ID of an already
    stored task (e.g. lets do 34)
    """
    guess_id = 0

    try:
        guess_id = int(task_name)
    except ValueError:
        return guess_id, False

    return guess_id, True
