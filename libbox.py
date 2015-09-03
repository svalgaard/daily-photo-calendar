#
#
#

import libpic
import libdpc

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
    sz = int((100-args.dateboxMiddleSize)/200 * h) - 4
    cbox = (x0, y0+sz+2, x1, y1-sz-2)

    # determine text to write
    texts = [args.dateboxTop, args.dateboxMiddle, args.dateboxBottom]
    texts = tuple(map(args.date.strftime, texts))
    libdpc.debug('datebox', 'texts to insert', texts)

    # find font sizes
    font = args.dateboxTopBottomFont
    font0 = libpic.fitFontSize(font, texts[0], (w, sz))
    font1 = libpic.fitFontSize(font, texts[2], (w, sz))
    fontS = font0 if font0.size <= font1.size else font1
    fontC = libpic.fitFontSize(args.dateboxMiddleFont, texts[1], cbox, True)

    # color
    color = args.dateboxColor

    libpic.textDraw(image, (x0, y0, x1, y0+sz), texts[0], color, fontS,
                    (libpic.CENTER, 0))
    libpic.textDraw(image, cbox, texts[1], color, fontC,
                    libpic.CENTER, True)
    libpic.textDraw(image, (x0, y1-sz, x1, y1), texts[2], color, fontS,
                    (libpic.CENTER, 0))


@boxType('e')
def events(args, f, image, box):
    image.drw.rectangle(box, (0, 255, 0), (0, 0, 255))
