# -*- encoding: utf-8 -*-
#
# Misc extensions for types for argparse
#
#

import re
import argparse
import sys
import os
import PIL.ImageFont
import locale
import datetime


def RECheck(formats, rege, func=None):
    '''Factory for checking argparse options against a regular expression.
    This can be used for type= arguments to the ArgumentParser
    add_argument() method.
    formats is used to show a human-readable version of the regular
    expression for error messages.

    rege is the regular expression to match against ($ is added at the
    end). If the expression contains groups, the groups are returned,
    otherwise, the options itself is returned.

    func is (optionally) called on the option to get the final result

    type=argp.REType('WIDTHxHEIGHT', r'(\d+)x(\d+)', lambda x: map(int, x))

    '''
    def check(s):
        m = re.match(rege + '$', s)
        if m:
            s = m.groups() if m.groups() else s
            return func(s) if func else s
        msg = '%r does not match the format %r' % (s, formats)
        raise argparse.ArgumentTypeError(msg)
    return check


def rangeCheck(pre, nmin, nmax):
    '''Factory for checking argparse options for being between the values
    nmin and name.  This can be used for type= arguments to the
    ArgumentParser.
    '''
    def check(s):
        try:
            s = pre(s)
        except ValueError:
            msg = '%r is not valid for the type %s'
            msg %= (s, pre.__doc__.split('(')[0])
            raise argparse.ArgumentTypeError(msg)
        if s < nmin or nmax < s:
            msg = '%r is not in the range %s to %s'
            msg %= (s, nmin, nmax)
            raise argparse.ArgumentTypeError(msg)
        return s
    return check

_allfonts = None


def fontCheck(name):
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


def maybeMore(subType, n=2, sep='~'):
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


def localeCheckSet(loc):
    if '.' not in loc:
        try:
            return locale.setlocale(locale.LC_ALL, (loc, 'UTF-8'))
        except locale.Error:
            pass

    msg = 'Unsupported locale %r. Use e.g. da_DK, en_US, etc.' % loc
    raise argparse.ArgumentTypeError(msg)


def dateCheck(s):
    try:
        dt = datetime.datetime.strptime(s, '%Y-%m-%d')
        return dt.date()
    except ValueError:
        msg = 'Date %r does not match the format YYYY-MM-DD' % s
        raise argparse.ArgumentTypeError(msg)
