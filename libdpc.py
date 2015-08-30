#
# -*- encoding: utf-8 -*-
#

import sys


VERBOSE = 1


def log(level, module, *msg):
    '''
    level = 0 is always printed
    level = 1 is normally printed
    level = 2 is only printed with -v options
    '''
    global VERBOSE
    if level <= VERBOSE:
        sys.stderr.write(u'[%s] %s\n' % (module, ' '.join(map(unicode, msg))))
        sys.stderr.flush()


def error(module, *msg):
    log(-1, module, *msg)
    log(-1, module, 'Fatal error - EXIT')
    sys.exit(1)
