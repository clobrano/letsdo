import os
import logging
try:
    from raffaello import Raffaello, Commission
    is_raffaello_available = True

    request = '''
\+[\w\-_]+=>color197_bold
\@[\w\-_]+=>color046
\#[\w\-_]+=>color202_bold
\d*h\s\d{1,2}m=>cyan_bold
\d{2,4}-\d{2}-\d{2}=>cyan_bold
^TaskID.*=>color009_bold
.*TODAY'S.*=>color009_bold
.*YESTERDAY'S.*=>color009_bold
'''
    raf = Raffaello(Commission(request).commission)
except ImportError:
    is_raffaello_available = False

if 'LETSDO_COLOR' in os.environ:
    do_color = is_raffaello_available
else:
    do_color = False

level = logging.INFO
logging.basicConfig(level=level, format='%(message)s')
logger = logging.getLogger(__name__)

def info(msg):
    global do_color
    if do_color:
        logger.info(raf.paint(msg))
    else:
        logger.info(msg)

def err (msg):
    logger.error (msg)

def warn (msg):
    loggern.warn (msg)

def dbg (msg):
    logger.debug (msg)


