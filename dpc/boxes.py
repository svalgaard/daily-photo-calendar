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


@boxType('m')
def month(args, f, image, box):
    image.drw.rectangle(box, (0, 0, 0), (0, 0, 255))


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
    font = args.dateboxTopBottomFont
    font0 = pics.fitFontSize(font, texts[0], (w, sz))
    font1 = pics.fitFontSize(font, texts[2], (w, sz))
    fontS = font0 if font0.size <= font1.size else font1
    fontC = pics.fitFontSize(args.dateboxMiddleFont, texts[1], cbox, True)

    # color
    color = args.dateboxColor

    pics.textDraw(image, (x0, y0, x1, y0+sz), texts[0], color, fontS,
                  (pics.CENTER, 0))
    pics.textDraw(image, cbox, texts[1], color, fontC,
                  pics.CENTER, True)
    pics.textDraw(image, (x0, y1-sz, x1, y1), texts[2], color, fontS,
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
                  args.eventboxTitleFont,
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
    font = pics.fitFontSize(args.eventboxFont, texts, (w, sz))
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
