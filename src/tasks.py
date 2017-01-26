import os
import datetime
import logging
import pickle
from persistance import Configuration
from reports import get_tasks

level = logging.INFO
logging.basicConfig(level=level, format='  %(message)s')
logger = logging.getLogger(__name__)
info = lambda x: logger.info(x)
err = lambda x: logger.error(x)
warn = lambda x: logger.warn(x)
dbg = lambda x: logger.debug(x)


class Task(object):
    def __init__(self, name='unknown', start=None, end=None, id=None):
        self.context = None
        self.end_date = None
        self.end_time = None
        self.name = None
        self.start_time = None
        self.tags = None
        self.work_time = datetime.timedelta()
        self.id = id
        self.pause = 0

        self.parse_name(name.strip())
        if start:
            self.start_time = str2datetime(start.strip()) #datetime.datetime.strptime(start.strip(), '%Y-%m-%d %H:%M')
        else:
            self.start_time = datetime.datetime.now()

        if end:
            self.end_time = str2datetime(end.strip()) #datetime.datetime.strptime(end.strip(), '%Y-%m-%d %H:%M')
            self.end_date = (self.end_time.strftime('%Y-%m-%d'))
            self.work_time = self.end_time - self.start_time
    
    @staticmethod
    def from_json(task_json):
        pass

    @staticmethod
    def get():
        TASK_FILENAME = Configuration().task_filename
        if Task.__is_running():
            with open(TASK_FILENAME, 'r') as f:
                return pickle.load(f)

    @staticmethod
    def stop(stop_time_str=None):
        task = Task.get()
        if not task:
            info('No task running')
            return

        if stop_time_str:
            stop_time = str2datetime(stop_time_str)
            if stop_time < task.start_time:
                warn('Given stop time (%s) is more recent than start time (%s)' % (stop_time, task.start_time))
                return False
            date = stop_time.strftime('%Y-%m-%d')
        else:
            stop_time = datetime.datetime.now()
            date = datetime.date.today()

        work_time_str = str(stop_time - task.start_time).split('.')[0][:-3]
        start_time_str = str(task.start_time).split('.')[0][:-3]
        stop_time_str = str(stop_time).split('.')[0][:-3]

        report = '%s,%s,%s,%s,%s\n' % (date, task.name, work_time_str, start_time_str, stop_time_str)
        DATA_FILENAME = Configuration().data_filename
        with open(DATA_FILENAME, mode='a') as f:
            f.writelines(report)

        TASK_FILENAME = Configuration().task_filename
        os.remove(TASK_FILENAME)
        status = ('Stopped task \'%s\' after %s of work' % (task.name, work_time_str))
        info(status)
        return True

    @staticmethod
    def change(name, pattern=None):
        task = Task.get()
        if task:
            if pattern:
                old_name = task.name
                name = old_name.replace(pattern, name)
            info('Renaming task \'%s\' to \'%s\'' % (task.name, name))
            task.parse_name(name)
            return task.__create()

        warn('No task running')

    @staticmethod
    def status():
        task = Task.get()
        if task:
            now = datetime.datetime.now()
            work = str(now - task.start_time).split('.')[0]
            info('Working on \'%s\' for %s' % (task.name, work))
            return True
        else:
            info('No task running')
            return False

    @staticmethod
    def __is_running():
        TASK_FILENAME = Configuration().task_filename
        exists = os.path.exists(TASK_FILENAME)
        dbg('is it running? %d' % exists)
        return exists

    def start(self):
        if not Task.__is_running():
            if self.__create():
                info('Starting task \'%s\'' % self.name)
                return Task.get()

            err('Could not create new task')
            return False

        warn('Another task is running')
        return True

    def __create(self):
        TASK_FILENAME = Configuration().task_filename
        with open(TASK_FILENAME, 'w') as f:
            pickle.dump(self, f)
            return True

    def parse_name(self, name):
        name = name.replace(',', ' ')
        self.name = name
        matches = re.findall('@[\w\-_]+', name)
        if len(matches) == 1:
            self.context = matches[0]
        matches = re.findall('\+[\w\-_]+', name)
        if len(matches) >= 1:
            self.tags = matches

    def __repr__(self):
        work_str = '%s' % str(self.work_time).split('.')[0]
        start_str = '%s' % self.start_time.strftime('%H:%M')
        end_str = '%s' % self.end_time.strftime('%H:%M')
        if self.id is not None:
            return '[%d] - %s| %s (%s -> %s) - %s' % (self.id, self.end_date, work_str, start_str, end_str, self.name)
        return '%s| %s (%s -> %s) - %s' % (self.end_date, work_str, start_str, end_str, self.name)

    def __eq__(self, other):
        return self.name == other.name

    def __ne__(self, other):
        return not (self.name == other.name)

    def __hash__(self):
        return hash((self.name))


def get_tasks(condition=None):
    tasks = []
    datafilename = Configuration().data_filename
    id = -1
    with open(datafilename) as f:
        for line in reversed(f.readlines()):
            dbg(line)
            fields = line.strip().split(',')
            t = Task(name=fields[1],
                     start=fields[3],
                     end=fields[4])
            try:
                same_task = tasks.index(t)
                t.id = tasks[same_task].id
                dbg('{task_name} has old id {id}'.format(task_name=t.name, id=t.id))
            except ValueError:
                id +=1
                t.id = id
                dbg('{task_name} has new id {id}'.format(task_name=t.name, id=t.id))
            tasks.append(t)

    return filter(condition, tasks)



