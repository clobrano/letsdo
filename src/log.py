'''
Logging facility
'''
import os
import sys
import logging

try:
    if 'LETSDO_COLOR' not in os.environ:
        RAFFAELLO = None
    else:
        from raffaello import Raffaello, parse_request

        REQUEST = r'''
\+[\w\-_]+=>color197_bold
\@[\w\-_]+=>color046
\#[\w\-_]+=>color202_bold
\d+[ms]=>cyan_bold
\d+h\s=>cyan_bold
\d{2,4}-\d{2}-\d{2}=>cyan_bold
'''
        RAFFAELLO = Raffaello(parse_request(REQUEST))
except ImportError as error:
    print('could not colorize output: {}'.format(error))
    RAFFAELLO = None

if 'LETSDO_DEBUG' in os.environ:
    LEVEL = logging.DEBUG
else:
    LEVEL = logging.INFO

logging.basicConfig(level=LEVEL, format='%(levelname)s %(funcName)s: %(message)s')
LOGGER = logging.getLogger(__name__)


def info(msg):
    '''Info level logging'''
    if RAFFAELLO:
        print(RAFFAELLO.paint(msg))
    else:
        print(msg)


def err(msg):
    '''Error level logging'''
    LOGGER.error(msg)


def warn(msg):
    '''Warning level logging'''
    LOGGER.warn(msg)


def dbg(msg):
    '''Debug level logging'''
    LOGGER.debug(msg)
