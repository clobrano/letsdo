import datetime
import re
from string import Formatter

def strfdelta(tdelta, fmt='{H:2}h {M:02}m', inputtype='timedelta'):
    """Convert a datetime.timedelta object or a regular number to a custom-
    formatted string, just like the stftime() method does for datetime.datetime
    objects.

    The fmt argument allows custom formatting to be specified.  Fields can
    include seconds, minutes, hours, days, and weeks.  Each field is optional.

    Some examples:
        '{D:02}d {H:02}h {M:02}m {S:02}s' --> '05d 08h 04m 02s' (default)
        '{W}w {D}d {H}:{M:02}:{S:02}'     --> '4w 5d 8:04:02'
        '{D:2}d {H:2}:{M:02}:{S:02}'      --> ' 5d  8:04:02'
        '{H}h {S}s'                       --> '72h 800s'

    The inputtype argument allows tdelta to be a regular number instead of the
    default, which is a datetime.timedelta object.  Valid inputtype strings:
        's', 'seconds',
        'm', 'minutes',
        'h', 'hours',
        'd', 'days',
        'w', 'weeks'
    """

    # Convert tdelta to integer seconds.
    if inputtype == 'timedelta':
        remainder = int(tdelta.total_seconds())
    elif inputtype in ['s', 'seconds']:
        remainder = int(tdelta)
    elif inputtype in ['m', 'minutes']:
        remainder = int(tdelta) * 60
    elif inputtype in ['h', 'hours']:
        remainder = int(tdelta) * 3600
    elif inputtype in ['d', 'days']:
        remainder = int(tdelta) * 86400
    elif inputtype in ['w', 'weeks']:
        remainder = int(tdelta) * 604800

    f = Formatter()
    desired_fields = [field_tuple[1] for field_tuple in f.parse(fmt)]
    possible_fields = ('W', 'D', 'H', 'M', 'S')
    constants = {'W': 604800, 'D': 86400, 'H': 3600, 'M': 60, 'S': 1}
    values = {}
    for field in possible_fields:
        if field in desired_fields and field in constants:
            values[field], remainder = divmod(remainder, constants[field])
    return f.format(fmt, **values)


def format_h_m(string):
    h, m = string.split(':')[0:2]
    return '{0}h {1}m'.format(h, m)
    #return ':'.join(string.split(':')[0:2])


def str2datetime(string):
    m = re.findall('\d{4}-\d{2}-\d{2} \d{2}:\d{2}', string)
    if len(m) != 0:
        string = m[0]
        return datetime.datetime.strptime(string, '%Y-%m-%d %H:%M')

    m = re.findall('\d{4}-\d{2}-\d{2} \d{2}.\d{2}', string)
    if len(m) != 0:
        string = m[0]
        return datetime.datetime.strptime(string, '%Y-%m-%d %H.%M')

    m = re.findall('\d{4}/\d{2}/\d{2} \d{2}:\d{2}', string)
    if len(m) != 0:
        string = m[0]
        return datetime.datetime.strptime(string, '%Y/%m/%d %H:%M')

    m = re.findall('\d{4}/\d{2}/\d{2} \d{2}.\d{2}', string)
    if len(m) != 0:
        string = m[0]
        return datetime.datetime.strptime(string, '%Y/%m/%d %H.%M')

    m = re.findall('\d{4}-\d{2}-\d{2}', string)
    if len(m) != 0:
        string = m[0]
        now_str = datetime.datetime.now().strftime('%H:%M')
        return datetime.datetime.strptime(string + ' ' + now_str,
                                          '%Y-%m-%d %H:%M')

    m = re.findall('\d{4}/\d{2}/\d{2}', string)
    if len(m) != 0:
        string = m[0]
        now_str = datetime.datetime.now().strftime('%H:%M')
        return datetime.datetime.strptime(string + ' ' + now_str,
                                          '%Y/%m/%d %H:%M')

    m = re.findall('\d{2}-\d{2} \d{2}:\d{2}', string)
    if len(m) != 0:
        string = m[0]
        year_str = datetime.datetime.today().strftime('%Y')
        return datetime.datetime.strptime(year_str + '-' + string,
                                          '%Y-%m-%d %H:%M')

    m = re.findall('\d{2}-\d{2} \d{2}.\d{2}', string)
    if len(m) != 0:
        string = m[0]
        year_str = datetime.datetime.today().strftime('%Y')
        return datetime.datetime.strptime(year_str + '-' + string,
                                          '%Y-%m-%d %H:%M')

    m = re.findall('\d{2}-\d{2}', string)
    if len(m) != 0:
        string = m[0]
        year_str = datetime.datetime.today().strftime('%Y')
        now_str = datetime.datetime.now().strftime('%H:%M')
        return datetime.datetime.strptime(
            year_str + '-' + string + ' ' + now_str, '%Y-%m-%d %H:%M')

    m = re.findall('\d{2}:\d{2}', string)
    if len(m) != 0:
        string = m[0]
        today_str = datetime.datetime.today().strftime('%Y-%m-%d')
        return datetime.datetime.strptime(today_str + ' ' + string,
                                          '%Y-%m-%d %H:%M')

    m = re.findall('\d:\d{2}', string)
    if len(m) != 0:
        string = m[0]
        today_str = datetime.datetime.today().strftime('%Y-%m-%d')
        return datetime.datetime.strptime(today_str + ' ' + string,
                                          '%Y-%m-%d %H:%M')

    m = re.findall('\d{2}.\d{2}', string)
    if len(m) != 0:
        string = m[0]
        today_str = datetime.datetime.today().strftime('%Y-%m-%d')
        return datetime.datetime.strptime(today_str + ' ' + string,
                                          '%Y-%m-%d %H.%M')

    m = re.findall('\d.\d{2}', string)
    if len(m) != 0:
        string = m[0]
        today_str = datetime.datetime.today().strftime('%Y-%m-%d')
        return datetime.datetime.strptime(today_str + ' ' + string,
                                          '%Y-%m-%d %H.%M')

    raise ValueError('Date format not recognized: %s' % string)


