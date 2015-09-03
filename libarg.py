#
# Misc type checking functions for argparse
#

import re
import argparse
import sys
import os
import PIL.ImageFont
import locale
import datetime


def REType(formats, rege):
    '''Factory for creating object types matched against a regular
    expression.  This can be used for type= arguments to the
    ArgumentParser add_argument() method.  formats is used to show a
    human-readable version of the regular expression.
    '''
    class CheckRE():
        def __call__(self, s):
            m = re.match(rege + '$', s)
            if m:
                return m.groups() if m.groups() else s
            msg = '%r does not match the format %r' % (s, formats)
            raise argparse.ArgumentTypeError(msg)
    return CheckRE()


def RangeCheck(type, nmin, nmax):
    '''Factory for creating object types matched against a regular
    expression.  This can be used for type= arguments to the
    ArgumentParser add_argument() method.
    '''
    class CheckRange():
        def __call__(self, s):
            try:
                s = type(s)
            except ValueError:
                msg = '%r is not valid for the type %s'
                msg %= (s, type.__doc__.split('(')[0])
                raise argparse.ArgumentTypeError(msg)
            if s < nmin or nmax < s:
                msg = '%r is not in the range %s to %s'
                msg %= (s, nmin, nmax)
                raise argparse.ArgumentTypeError(msg)
            return s
    return CheckRange()

_allfonts = None


def Font(name):
    '''Check that name is a valid PIL/Pillow font'''
    global _allfonts

    if _allfonts is None:
        _allfonts = {}
        for dn in ('.',
                   sys.path[0],
                   '/Library/Fonts/'):
            for dirpath, dirnames, filenames in os.walk(dn):
                for fn in filenames:
                    lfn = os.path.join(dirpath, fn)
                    key, ext = os.path.splitext(fn.lower().replace(' ', '_'))
                    if ext == '.ttf' and key not in _allfonts:
                        _allfonts[key] = lfn

    if ':' in name:
        name, size = name.rsplit(':', 2)
        dsize, size = int(size), int(size)
    else:
        dsize, size = None, 10
    name = name.lower()

    for sn, lfn in sorted(_allfonts.items()):
        if name == sn:
            # found!
            font = PIL.ImageFont.truetype(lfn, size)
            font.dlfn = lfn
            font.dsize = dsize
            return font

    # font not found
    print('Font %r not found' % name)
    print('Available fonts:')
    for sn, lfn in sorted(_allfonts.items()):
        print ('  %s (found in %s)' % (sn, lfn))

    raise argparse.ArgumentTypeError('Font %r not found' % name)


class More:
    def __init__(self, arg):
        self.arg = arg

    def __getitem__(self, i):
        return self.arg[i]


def deMore(args, n):
    for (k, v) in args.__dict__.items():
        if type(v) == More:
            args.__dict__[k] = v[n]


def maybeMore(subType, n=2, sep=':'):
    def check(s):
        sp = s.split(sep)
        if len(sp) == 1:
            res = subType(s)
            return More((res,)*n)
        elif len(sp) == n:
            return More(tuple(map(subType, sp)))

        raise ValueError('You should either not use any %r or exactly %d' %
                         (sep, n-1))
    return check


def setLocale(loc):
    if '.' not in loc:
        try:
            return locale.setlocale(locale.LC_ALL, (loc, 'UTF-8'))
        except locale.Error:
            pass

    msg = 'Unsupported locale %r. Use e.g. da_DK, en_US, etc.' % loc
    raise argparse.ArgumentTypeError(msg)


def dateType(s):
    try:
        dt = datetime.datetime.strptime(s, '%Y-%m-%d')
        return dt.date()
    except ValueError:
        msg = 'Date %r does not match the format YYYY-MM-DD' % s
        raise argparse.ArgumentTypeError(msg)
