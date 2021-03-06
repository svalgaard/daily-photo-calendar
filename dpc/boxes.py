#
# -*- encoding: utf-8 -*-
#

import datetime
import locale

from . import log
from . import pics

BOX_TYPES = {}


def boxType(name):
    def wrap(f):
        BOX_TYPES[name] = f
        return f
    return wrap


def getFuncForBoxType(name):
    if name in BOX_TYPES:
        return BOX_TYPES[name]
    raise ValueError('Unknow boxtype %r' % name)


def getBoxTypes():
    return list(sorted(BOX_TYPES.keys()))


@boxType('_')
def noop(args, f, image, box):
    # no-op, i.e., nothing here
    pass


@boxType('d')
def datebox(args, f, image, box):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    sz = int(args.dateboxTopSize / 100 * h)
    cbox = (x0, y0+sz+2, x1, y1-sz-2)

    # determine text to write
    texts = [args.dateboxTop, args.dateboxMiddle, args.dateboxBottom]
    texts = tuple(map(args.date.strftime, texts))
    log.debug('datebox', 'texts to insert', texts)

    # find font sizes
    fontS = pics.fitFontSize(args.fontRegular, [texts[0], texts[2]], (w, sz))

    # color
    color = args.dateboxColor

    pics.textDraw(image, (x0, y0, x1, y0+sz), texts[0], color, fontS,
                  (pics.CENTER, 0))
    pics.textDraw(image, cbox, texts[1], color, args.fontBold,
                  pics.CENTER, True, True)
    pics.textDraw(image, (x0, y1-sz, x1, y1), texts[2], color, fontS,
                  (pics.CENTER, 0))


@boxType('s')
def simplebox(args, f, image, box):
    ''' left MIDDLE right, e.g, Thursday 28 October'''
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0

    # determine text to write
    texts = [args.simpleboxLeft,
             args.simpleboxMiddle,
             args.simpleboxRight]
    texts = tuple(map(args.date.strftime, texts))
    log.debug('datebox', 'texts to insert', texts)

    # draw middle text
    color = args.dateboxColor
    fontM = pics.fitFontSize(args.fontBold, texts[1], (w, h), True)
    pics.textDraw(image, box, texts[1], color, fontM, pics.CENTER, True)
    spaceUsed = fontM.getmask(texts[1]).size

    # draw left/right text
    if w - spaceUsed[0] > 10:
        leftRight = True
        space = [(w-spaceUsed[0])//2, h]
        if space[0] > spaceUsed[1]//2:
            space[0] -= spaceUsed[1]//4
    elif h - spaceUsed[1] > 10:
        leftRight = False
        space = [w, (h-spaceUsed[1])//2]
        if space[1] > spaceUsed[1]//2:
            space[1] -= spaceUsed[1]//4
    else:
        log.debug('simplebox', 'No space left for left/right text',
                  (w, h), spaceUsed)
        return

    fontLR = pics.fitFontSize(args.fontRegular,
                              [texts[0], texts[2]], space)

    if fontLR.size > fontM.size//2:
        fontLR = pics.scaleFont(fontLR, fontM.size//2)

    if leftRight:
        # actually do left/right text
        pics.textDraw(image,
                      (x0, y0, x0+space[0], y0+space[1]),
                      texts[0], color, fontLR,
                      (-1, pics.CENTER))
        pics.textDraw(image,
                      (x1-space[0], y1-space[1], x1, y1),
                      texts[2], color, fontLR,
                      (0, pics.CENTER))
    else:
        pics.textDraw(image,
                      (x0, y0, x0+space[0], y0+space[1]),
                      texts[0], color, fontLR,
                      (pics.CENTER, -1))
        pics.textDraw(image,
                      (x1-space[0], y1-space[1], x1, y1),
                      texts[2], color, fontLR,
                      (pics.CENTER, 0))


@boxType('e')
def events(args, f, image, box):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    sz = int(args.eventboxTitleSize / 100 * h)

    # Title
    title = args.date.strftime(args.eventboxTitle)
    tbox = (x0, y0, x1, y0+sz)
    pics.textDraw(image, tbox, title, args.eventboxTitleColor,
                  args.fontBold,
                  (0, pics.CENTER), False, True)

    # Find applicable events
    end = args.date + datetime.timedelta(days=args.eventboxRange)
    evs = list(ev for ev in args.events if ev.between(args.date, end))

    mx = h//sz
    evs = evs[:mx]
    if not evs:
        log.debug('events', 'NO EVENTS TO SHOW')
    texts = []
    for i, ev in enumerate(evs):
        dt = ev.date.strftime(shortDateFormat())
        text = '%s: %s' % (dt, ev.text)
        log.debug('events', '%r ==> %s' % (ev, text))
        texts.append(text)
    font = pics.fitFontSize(args.fontRegular, texts, (w, sz))
    for i, text in enumerate(texts):
        ebox = (x0, y0+sz*(i+1), x1, y0+sz*(i+2))
        pics.textDraw(image, ebox, text,
                      args.eventboxTitleColor, font,
                      (0, pics.CENTER))

    # fixme
    # image.drw.rectangle(box, (0, 255, 0), (0, 0, 255))


def shortDateFormat():
    '''Return short date format for any locale - this probably breaks for some
    locales'''
    fmt = locale.nl_langinfo(locale.D_FMT)
    fmt = fmt.replace('%Y', '').replace('%y', '')
    fmt = fmt.strip('/-.')
    return fmt


@boxType('m')
def month(args, f, image, box):
    '''Draw a calendar. Always 6 weeks + names of days'''
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0

    w0 = int(w//7)
    h0 = int(h//6.7)
    ht = h - 6*h0

    # Which month are we looking at?
    day0 = args.date.replace(day=1)
    while day0.weekday() != args.monthboxFirstDay:
        day0 -= datetime.timedelta(1)

    # "Title"
    days = list((day0 + datetime.timedelta(i)).strftime('%a')
                for i in range(7))
    font = pics.fitFontSize(args.fontBold, days, (w0-4, ht-4), True)
    for i in range(7):
        bx = (x0 + w0*i, y0, x0 + w0*(i+1), y0+ht)
        image.drw.rectangle(bx,
                            args.monthboxTitleBgColor,
                            args.monthboxTitleBorderColor)
        pics.textDraw(image, bx, days[i],
                      args.monthboxTitleColor, font)

    font = pics.fitFontSize(args.fontBold, '88', (w0-8, h0-8), True)
    evs = args.events[:]
    for week in range(6):
        for i in range(7):
            day = day0+datetime.timedelta(week*7+i)

            # determine whether today should be marked
            markAsDayOff = False
            while evs[0].date < day:
                del evs[0]
            while evs[0].date == day:
                if evs[0].markAsDayOff():
                    markAsDayOff = True
                del evs[0]

            bx = (x0 + w0*i,     y0+ht+h0*week,
                  x0 + w0*(i+1), y0+ht+h0*(week+1))
            if day.month != args.date.month:
                color = args.monthboxOthermonthColor
                bgcolor = args.monthboxOthermonthBgColor
            elif day == args.date:
                color = args.monthboxTodayColor
                bgcolor = args.monthboxTodayBgColor
            elif day.weekday() in args.monthboxDayoff or markAsDayOff:
                color = args.monthboxDayoffColor
                bgcolor = args.monthboxDayoffBgColor
            else:
                color = args.monthboxDefaultColor
                bgcolor = args.monthboxDefaultBgColor

            image.drw.rectangle(bx,
                                bgcolor,
                                None and args.monthboxBorderColor)
            pics.textDraw(image, bx, str(day.day), color, font)
