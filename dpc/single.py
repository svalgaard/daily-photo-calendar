#! /usr/bin/env python3
# -*- encoding: utf-8 -*-
#
#

import argparse
import re
import sys
import PIL.ImageColor
import locale

from . import log
from . import pics
from . import argp
from . import boxes

FONT_BOLD = 'Raleway-Bold'
FONT_REGULAR = 'Raleway-Regular'


def addPicture(image, args, goTOP=None):
    TOP = args.format[0] == 't' if goTOP is None else goTOP
    log.debug('addPicture', 'At top?', TOP)

    # handle portrait images
    if not args.image.isLandscape():
        if TOP:
            log.debug('addPicture', 'portrait image: rotating CW')
            args.image = args.image.rotateCW()
            image = addPicture(image.rotateCW(), args).rotateCCW()
            args.image = args.image.rotateCCW()
        else:
            log.debug('addPicture', 'portrait image: rotating CCW')
            args.image = args.image.rotateCCW()
            image = addPicture(image.rotateCCW(), args, True).rotateCW()
            args.image = args.image.rotateCW()
        return image

    # margin in pixels
    mpO = args.size[1] * args.marginOuter / 100
    mpI = args.size[1] * args.marginInner / 100
    log.debug('handle', 'Margins in pixels:', mpO, mpI)

    x, y, w, h = 0, 0, image.size[0], image.size[1]
    h = int(image.size[0] / args.ratio)
    if not TOP:
        y = image.size[1] - h

    pimg = pics.cropImage(args.image, (w, h), False)
    image.paste(pimg, (x, y))
    log.debug('handle', (x, y, w, h), 'Input image pasted')

    if args.text:
        # we are always slightly above or below the image
        th = args.textFont.dsize
        if not th or th <= 0:
            th = int(mpI)
        if TOP:
            box = pics.intBox((mpO, h, w-mpO, h + th))  # text below image
        else:
            box = pics.intBox((mpO, y - th, w-mpO, y))
        font = pics.scaleFont(args.textFont, 2*th//3)

        pics.textDraw(image, box,
                      args.text, args.textColor,
                      font, position=(-1, pics.CENTER))
        log.debug('handle', box, 'Text', repr(args.text))

    # determine location of remaining space
    a, b, c, d = mpO, mpO, image.size[0] - mpO, image.size[1] - mpO
    if TOP:
        # at the bottom
        b = h + mpI
    else:
        d = y - mpI

    image.box = pics.intBox((a, b, c, d))
    return image


def findContentBoxes(image, args):
    log.debug('handle', image.box, 'Content-area')
    fmts = args.format[1]

    mpI = args.size[1] * args.marginInner / 100

    boxes, boxCount = [], len(fmts)
    w, h = image.box[2]-image.box[0], image.box[3]-image.box[1]
    for i in range(boxCount):
        a, b, c, d = image.box
        if w > h:
            # landscape
            boxw = (w - mpI*(boxCount-1)) / boxCount
            a += (boxw + mpI) * i
            c = a + boxw
        else:
            boxh = (h - mpI*(boxCount-1)) / boxCount
            b += (boxh + mpI) * i
            d = b + boxh
        boxes.append((fmts[i], pics.intBox((a, b, c, d))))
    return boxes


def handle(args):
    global image

    log.debug('handle', 'Format used', args.format)

    image = pics.decorateImage(PIL.Image.new('RGB', args.size, args.bgcolor))
    image = addPicture(image, args)

    cboxes = findContentBoxes(image, args)
    for i, (f, cbox) in enumerate(cboxes):
        fn = boxes.getFuncForBoxType(f)
        log.debug('handle', cbox, 'Subbox', i, 'format', f)
        fn(args, f, image, cbox)
    image.show()


def mmarg(arg, **args):
    if not arg.type:
        arg.type = str
    arg.type = argp.maybeMore(arg.type, **args)
    arg.mm = True
    return arg


def main():
    desc = '''Create a single calendar page.

In all cases where it makes sense and unless otherwise noted, all
options can be supplied with two suboptions for landscape
resp. portrait images. The two options should be separated with \\t
e.g., --margin-inner 4\\t5 (meaning 4% for landscape pictures and 5%
for portrait pictures).'''
    parser = argparse.ArgumentParser(description=desc)

    parser.add_argument('-v', '--verbose', dest='verbose', default=False,
                        help='Be more verbose',
                        action='store_true')

    pgrp = parser.add_argument_group('General setup')
    mmarg(pgrp.add_argument('--size', dest='size', default='1200x1050',
                            help='size of a page in pixels '
                            '(default %(default)s)',
                            metavar='SIZE',
                            type=argp.REType('WIDTHxHEIGHT', r'\d+x\d+')))
    mmarg(pgrp.add_argument('--margin-outer', dest='marginOuter',
                            default='4.5', metavar='RATIO',
                            help='outer margin in %% (default %(default)s)',
                            type=argp.RangeCheck(float, 0, 40)))
    mmarg(pgrp.add_argument('--margin-inner', dest='marginInner',
                            metavar='RATIO', default='2.25',
                            help='inner margin in %% (default %(default)s)',
                            type=argp.RangeCheck(float, 0, 20)))
    reformat = r'([tb])((?:%s)+)' % '|'.join(boxes.getBoxTypes())
    mmarg(pgrp.add_argument('-f', '--format', dest='format',
                            default='tmde',
                            help='format of each page (default %(default)s)',
                            metavar='FORMAT',
                            type=argp.REType(reformat, reformat)))
    mmarg(pgrp.add_argument('--bgcolor', dest='bgcolor', default='#DEDEDE',
                            help='background color (default %(default)s)',
                            metavar='COLOR',
                            type=PIL.ImageColor.getrgb))
    pgrp.add_argument('--locale', dest='locale',
                      default=locale.getdefaultlocale()[0],
                      help='Locale to use for dates etc (default %(default)s)',
                      metavar='LOCALE',
                      type=argp.setLocale)
    pgrp.add_argument('-d', '--date', dest='date', required=True,
                      help='Date to show', metavar='DATE',
                      type=argp.dateType)

    pgrp = parser.add_argument_group('Picture')
    pgrp.add_argument('-p', '--picture', dest='imagefd', default=None,
                      help='filename of picture to use',
                      metavar='FILENAME', required=True,
                      type=argparse.FileType('rb'))
    mmarg(pgrp.add_argument('-r', '--ratio', dest='ratio',
                            default='1.5\t1.3333333',
                            help='ratio to crop all images to '
                            '(default %(default)s)',
                            metavar='RATIO',
                            type=argp.RangeCheck(float, 0, 10)))
    pgrp.add_argument('--text', dest='text', default='',
                      help='text to show below image (default none)',
                      metavar='TEXT',
                      type=str)
    mmarg(pgrp.add_argument('--text-font', dest='textFont',
                            default=FONT_REGULAR,
                            help='font for text to show below image '
                            '(default %(default)s)',
                            metavar='FONT',
                            type=argp.Font))
    mmarg(pgrp.add_argument('--text-color', dest='textColor',
                            default='#000000',
                            help='color of the text to show below image '
                            '(default %(default)s)',
                            metavar='COLOR',
                            type=PIL.ImageColor.getrgb))

    pgrp = parser.add_argument_group('Datebox (d)')
    mmarg(pgrp.add_argument('--datebox-top', dest='dateboxTop',
                            default='%A uge %V',
                            help='datetext to show above '
                            '(default %(default)s)',
                            metavar='CONTENT'))
    mmarg(pgrp.add_argument('--datebox-middle', dest='dateboxMiddle',
                            default='%e',
                            help='datetext to show in the middle '
                            '(default %(default)s)',
                            metavar='CONTENT'))
    mmarg(pgrp.add_argument('--datebox-bottom', dest='dateboxBottom',
                            default='%B %Y',
                            help='datetext to show below '
                            '(default %(default)s)',
                            metavar='CONTENT'))
    mmarg(pgrp.add_argument('--datebox-color', dest='dateboxColor',
                            default='#000000',
                            help='color of the datebox text '
                            '(default %(default)s)',
                            metavar='COLOR',
                            type=PIL.ImageColor.getrgb))
    mmarg(pgrp.add_argument('--datebox-font', dest='dateboxTopBottomFont',
                            default=FONT_REGULAR,
                            help='font for the top/bottom part of the datebox '
                            '(default %(default)s)',
                            metavar='FONT',
                            type=argp.Font))
    mmarg(pgrp.add_argument('--datebox-middle-font', dest='dateboxMiddleFont',
                            default=FONT_BOLD,
                            help='font for the middle part of the datebox '
                            '(default %(default)s)',
                            metavar='FONT',
                            type=argp.Font))
    mmarg(pgrp.add_argument('--datebox-middle-size', dest='dateboxMiddleSize',
                            default=60,
                            help='height of datebox in %% to use for '
                            'date-middle (default %(default)s)',
                            metavar='SIZE',
                            type=argp.RangeCheck(float, 0, 100)))

    pgrp = parser.add_argument_group('Events (e)')
    pgrp.add_argument('-e', '--event-file', dest='eventboxTop',
                      default=None, action='append',
                      help='eventfile to use - use several times '
                      'to use multiple files '
                      '(default %(default)s)',
                      type=argparse.FileType('r'),
                      metavar='FILE')
    mmarg(pgrp.add_argument('--eventbox-title', dest='eventboxTitle',
                            default='%A:',
                            help='datetext to show above the events '
                            '(default %(default)s)',
                            metavar='CONTENT'))
    mmarg(pgrp.add_argument('--eventbox-title-font', dest='eventboxTitleFont',
                            default=FONT_BOLD,
                            help='font for the title of the event box '
                            '(default %(default)s)',
                            metavar='FONT',
                            type=argp.Font))
    mmarg(pgrp.add_argument('--eventbox-font', dest='eventboxFont',
                            default=FONT_REGULAR,
                            help='font for the middle part of the event box '
                            '(default %(default)s)',
                            metavar='FONT',
                            type=argp.Font))

    args = parser.parse_args()

    try:
        # The file has already been opened
        args.image = pics.decorateImage(PIL.Image.open(args.imagefd))
    except IOError:
        log.error('main', '%r does not contain valid image data' %
                  args.imagefd.name)
        sys.exit(1)

    # use options depending on whether it's a landscape or portrait image
    argp.deMore(args, 0 if args.image.isLandscape() else 1)

    # Now check some of options
    log.VERBOSE = 2 if args.verbose else 1

    args.size = tuple(map(int, args.size.split('x')))

    formatsp = r'(%s)' % '|'.join(boxes.getBoxTypes())
    formatsp = tuple(filter(None, re.split(formatsp, args.format[1])))
    args.format = args.format[0], formatsp

    handle(args)


if __name__ == '__main__':
    main()