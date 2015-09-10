# -*- encoding: utf-8 -*-
# Events
# functions to parse events
'''
UTF-8 text files

Lines starting with # are ignored

DATE;TYPE;TEXT

DATE
----
Dates must be in the format YYYY-MM-DD.
OR in the format EASTER+DD or EASTER-DD
where DD is a number of days after/before easter.

Use the year 8888, if the year should not be used/shown, e.g.,
Christmas day, 8888-12-25

TYPE
----
 'd'  # birthday / wedding adds text with (xx years)
 'g'  # general holiday/event
 'm'  # general holiday/event day off (marked as Sunday)
 '='  # do not repeat this event yearly

Dates with 8888 or EASTER implies =

TEXT
----
Any non empty string. If type contains d, (1 year) or (xx years) is added

'''

import datetime
import locale
import re

from . import log

# MIN/MAX year for which we generate events
MINYEAR = 1980
MAXYEAR = 2100


def yearText(n):
    loc = locale.getlocale()
    if isinstance(loc, tuple):
        loc = loc[0]
    if loc and loc.startswith('da'):
        yt = '%d år', '%d år'
    elif loc and loc.startswith('de'):
        yt = '%d Jahre', '%d Jahren'
    else:
        yt = '%d year', '%d years'
    yt = yt[1] if n != 1 else yt[0]
    return yt % n


def easter(year):
    '''Returns date of Easter as a date object using magic
From http://code.activestate.com/recipes/576517/'''
    a = year % 19
    b = year // 100
    c = year % 100
    d = (19 * a + b - b // 4 - ((b - (b + 8) // 25 + 1) // 3) + 15) % 30
    e = (32 + 2 * (b % 4) + 2 * (c // 4) - d - (c % 4)) % 7
    f = d + e - 7 * ((a + 11 * d + 22 * e) // 451) + 114
    month = f // 31
    day = f % 31 + 1
    return datetime.date(year, month, day)


class Event:
    def __init__(self, date, tp, text):
        self.date = date
        self.tp = tp
        self.text = text

    def between(self, start, end):
        return start <= self.date <= end

    def markAsDayOff(self):
        return 'm' in self.tp

    def __lt__(self, other):
        return self.date < other.date

    def __repr__(self):
        return 'Event(%r, %r, %r)' % (self.date, self.tp, self.text)

def readEventFile(fd):
    events = []
    for i, line in enumerate(fd):
        premsg = 'events-%s:%d' % (fd.name, i)

        line = line.strip()
        if not line or line[0] == '#':
            continue
        sp = re.split(' *; *', line, 2)
        if len(sp) != 3:
            log.debug(premsg, 'Too few ; - %r' % line)
            continue
        dt, tp, text = sp

        if not dt:
            log.error(premsg, 'Empty date %r' % line)
            continue
        if not tp:
            log.error(premsg, 'Empty type %r' % line)
            continue
        if not text:
            log.error(premsg, 'Empty text %r' % line)
            continue

        # check the type
        tp = tp.lower()
        tp2 = re.sub('[^dgm=]', '', tp)
        if not tp2:
            log.error(premsg, 'No recognised types in %r' % tp)
            continue
        elif tp != tp2:
            log.debug(premsg, 'Type reduced from %s to %r' % (tp, tp2))
            tp = tp2
        tp = ''.join(sorted(set(tp)))
        if 'd' in tp and 'g' in tp:
            log.debug(premsg, 'Type cannot contain both d and g %r' % tp)
            tp = tp.remove('g')

        # check the date
        m = re.match(r'(?i)^easter([-+]\d+)?$', dt)
        if m:
            delta = m.group(1)
            delta = 0 if delta is None else int(delta)
            delta = datetime.timedelta(delta)

            if '=' not in tp:
                tp += '='
            if 'd' in tp:
                tp = tp.remove('d')

            for year in range(MINYEAR, MAXYEAR+1):
                date = easter(year) + delta
                events.append(Event(date, tp, text))
            continue

        # normal date
        try:
            dt = datetime.datetime.strptime(dt, '%Y-%m-%d')
            dt = dt.date()
        except ValueError:
            log.debug(premsg, 'Unrecognised date %s' % dt)
            continue

        if dt.year == 8888:
            if '=' not in tp:
                tp += '='
            for year in range(MINYEAR, MAXYEAR+1):
                date = dt.replace(year=year)
                events.append(Event(date, tp, text))
            continue

        # regular date, e.g., birthday
        if '=' in tp:
            events.append(Event(dt, tp, text))
            continue

        for year in range(max(dt.year, MINYEAR), MAXYEAR+1):
            date = dt.replace(year=year)
            txt = text
            if 'd' in tp:
                txt += ' (%s)' % yearText(year-dt.year)
            events.append(Event(date, tp, txt))
        continue

    events.sort()
    return events
