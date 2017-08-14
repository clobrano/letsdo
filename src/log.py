'''
Logging facility
'''
import os
import logging

try:
    if 'LETSDO_COLOR' not in os.environ:
        RAFFAELLO = None
    else:
        from raffaello import Raffaello, Commission

        REQUEST = r'''
\+[\w\-_]+=>color197_bold
\@[\w\-_]+=>color046
\#[\w\-_]+=>color202_bold
\d+[ms]=>cyan_bold
\d+h\s=>cyan_bold
\d{2,4}-\d{2}-\d{2}=>cyan_bold
'''
        RAFFAELLO = Raffaello(Commission(REQUEST).commission)
except ImportError:
    RAFFAELLO = None

if 'LETSDO_DEBUG' in os.environ:
    LEVEL = logging.DEBUG
else:
    LEVEL = logging.INFO

logging.basicConfig(level=LEVEL, format='%(message)s')
LOGGER = logging.getLogger(__name__)


def info(msg):
    '''Info level logging'''
    if RAFFAELLO:
        LOGGER.info(RAFFAELLO.paint(msg))
    else:
        LOGGER.info(msg)


def err(msg):
    '''Error level logging'''
    LOGGER.error(msg)


def warn(msg):
    '''Warning level logging'''
    LOGGER.warn(msg)


def dbg(msg):
    '''Debug level logging'''
    LOGGER.debug(msg)
