#! /usr/bin/env python3
# -*- encoding: utf-8 -*-
#
#

import argparse
import re
import sys
import PIL.ImageColor
import locale
import os

from . import log
from . import pics
from . import argp
from . import boxes
from . import events

FONT_BOLD = 'roboto-black'
FONT_REGULAR = 'roboto-medium'


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

    x, y, w, h = 0, 0, image.size[0], image.size[1]
    h = int(image.size[0] / args.ratio)
    if not TOP:
        y = image.size[1] - h

    pimg = pics.cropImage(args.image, (w, h), False)
    image.paste(pimg, (x, y))
    log.debug('handle', (x, y, w, h), 'Input image pasted')

    if args.text:
        # we are always slightly above or below the image
        th = args.marginInner
        x0, x1 = args.marginOuter, w-args.marginOuter
        if TOP:
            # text below image
            box = pics.intBox((x0, h, x1, h + th))
        else:
            box = pics.intBox((x0, y - th, x1, y))
        font = pics.scaleFont(args.fontRegular, 2*th//3)

        pics.textDraw(image, box,
                      args.text, args.textColor,
                      font, position=(-1, pics.CENTER))
        log.debug('handle', box, 'Text', repr(args.text))

    # determine location of remaining space
    a, b = args.marginOuter, args.marginOuter
    c, d = image.size[0] - args.marginOuter, image.size[1] - args.marginOuter
    if TOP:
        # at the bottom
        b = h + args.marginInner
    else:
        d = y - args.marginInner

    image.box = pics.intBox((a, b, c, d))
    return image


def findContentBoxes(image, args):
    log.debug('handle', image.box, 'Content-area')
    fmts = args.format[1]

    boxes, boxCount = [], len(fmts)
    w, h = image.box[2]-image.box[0], image.box[3]-image.box[1]
    for i in range(boxCount):
        a, b, c, d = image.box
        if w > h:
            # landscape
            boxw = (w - args.marginInner*(boxCount-1)) / boxCount
            a += (boxw + args.marginInner) * i
            c = a + boxw
        else:
            boxh = (h - args.marginInner*(boxCount-1)) / boxCount
            b += (boxh + args.marginInner) * i
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

    if args.outfn:
        dn = os.path.dirname(args.outfn)
        if not os.path.isdir(dn):
            log.debug('handle', 'mkdir', dn)
            os.makedirs(dn)
        log.debug('handle', 'saving result in', args.outfn)
        image.save(args.outfn)
    if args.show:
        image.show()


def mmarg(arg, **args):
    if not arg.type:
        arg.type = str
    arg.type = argp.maybeMore(arg.type, **args)
    arg.mm = True
    return arg


def main():
    desc = '''Create a single calendar page.

For most options, you can give two suboptions for landscape
resp. portrait images. The two options should be separated with ~
e.g., --margin-inner 4~5 (meaning 4% for landscape pictures and 5%
for portrait pictures).'''
    parser = argparse.ArgumentParser(description=desc)

    parser.add_argument('-v', '--verbose', dest='verbose', default=False,
                        help='Be more verbose',
                        action='store_true')

    pgrp = parser.add_argument_group('(semi)required options')
    pgrp.add_argument('-d', '--date', dest='date', required=True,
                      help='Date to show', metavar='DATE',
                      type=argp.dateCheck)
    pgrp.add_argument('-o', '--output', dest='outfn', default=None,
                      help='filename of output file',
                      metavar='FILENAME')
    pgrp.add_argument('--skip-if-output-exists', dest='skipIfExists',
                      help='do nothing if the output file already exists '
                      'and is a valid image file',
                      action='store_true')
    pgrp.add_argument('--show', dest='show', action='store_true',
                      help='Show result, i.e., open a GUI window')

    pgrp = parser.add_argument_group('general appearance')
    reformat = r'([tb])((?:%s)+)' % '|'.join(boxes.getBoxTypes())
    mmarg(pgrp.add_argument('-f', '--format', dest='format',
                            default='tmde~tdme',
                            help='format of each page (default %(default)s)',
                            metavar='FORMAT',
                            type=argp.RECheck(reformat, reformat)))
    mmarg(pgrp.add_argument('--size', dest='size', default='1200x1050',
                            help='size of a page in pixels. Usually '
                            '300 dpi is fine, i.e., 300 pixels/2.5 cm '
                            '(default %(default)s)',
                            metavar='SIZE',
                            type=argp.RECheck('WIDTHxHEIGHT', r'(\d+)x(\d+)',
                                              lambda x: tuple(map(int, x)))))
    mmarg(pgrp.add_argument('--margin-outer', dest='marginOuter',
                            default='4.5', metavar='RATIO',
                            help='outer margin in %% (default %(default)s)',
                            type=argp.rangeCheck(float, 0, 40)))
    mmarg(pgrp.add_argument('--margin-inner', dest='marginInner',
                            metavar='RATIO', default='2.25',
                            help='inner margin in %% (default %(default)s)',
                            type=argp.rangeCheck(float, 0, 20)))
    mmarg(pgrp.add_argument('--bgcolor', dest='bgcolor', default='#FFFFFF',
                            help='background color (default %(default)s)',
                            metavar='COLOR',
                            type=PIL.ImageColor.getrgb))
    pgrp.add_argument('--locale', dest='locale',
                      default=locale.getdefaultlocale()[0],
                      help='Locale to use for dates etc (default %(default)s)',
                      metavar='LOCALE',
                      type=argp.localeCheckSet)
    pgrp.add_argument('--font-dir', dest='fontDirs',
                      default=argp.FONT_DNS,
                      help='add directory to search for fonts. Note you '
                      'must use this option before using any other font '
                      'options (default %s)' % ', '.join(argp.FONT_DNS),
                      metavar='FONTDIR')
    pgrp.add_argument('--font-regular', dest='fontRegular',
                      default=FONT_REGULAR,
                      help='text font for text '
                      '(default %(default)s)',
                      metavar='FONT',
                      type=argp.fontCheck)
    pgrp.add_argument('--font-bold', dest='fontBold',
                      default=FONT_BOLD,
                      help='text font for emphasised text '
                      '(default %(default)s)',
                      metavar='FONT',
                      type=argp.fontCheck)

    pgrp = parser.add_argument_group('picture')
    pgrp.add_argument('-p', '--picture', dest='imagefd', default=None,
                      help='filename of picture to use',
                      metavar='FILENAME', required=True,
                      type=argparse.FileType('rb'))
    mmarg(pgrp.add_argument('-r', '--ratio', dest='ratio',
                            default='1.5~1.3333333',
                            help='ratio to crop all images to '
                            '(default %(default)s)',
                            metavar='RATIO',
                            type=argp.rangeCheck(float, 0, 10)))
    pgrp.add_argument('--text', dest='text', default='',
                      help='text to show below image (default none)',
                      metavar='TEXT',
                      type=str)
    mmarg(pgrp.add_argument('--text-color', dest='textColor',
                            default='#000000',
                            help='color of the text to show below image '
                            '(default %(default)s)',
                            metavar='COLOR',
                            type=PIL.ImageColor.getrgb))

    pgrp = parser.add_argument_group('datebox (d)')
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
    mmarg(pgrp.add_argument('--datebox-top-size', dest='dateboxTopSize',
                            default=20,
                            help='height of datebox in %% to use for each of'
                            'date-top and date-bottom (default %(default)s)',
                            metavar='SIZE',
                            type=argp.rangeCheck(float, 1, 49)))

    pgrp = parser.add_argument_group('events (e)')
    pgrp.add_argument('-e', '--event-file', dest='events',
                      default=None, action='append',
                      help='eventfile to use - use several times '
                      'to use multiple files '
                      '(default %(default)s)',
                      type=argparse.FileType('r'),
                      metavar='FILE')
    mmarg(pgrp.add_argument('--eventbox-range', dest='eventboxRange',
                            default=14,
                            help='maximum number of days in the future for '
                            'shown events '
                            '(default %(default)s)',
                            metavar='DAYS',
                            type=argp.rangeCheck(int, 0, 365)))
    mmarg(pgrp.add_argument('--eventbox-title', dest='eventboxTitle',
                            default='%B:',
                            help='datetext to show above the events '
                            '(default %(default)s)',
                            metavar='CONTENT'))
    mmarg(pgrp.add_argument('--eventbox-title-size', dest='eventboxTitleSize',
                            default=15,
                            help='height of eventbox in %% to use for '
                            'the title (default %(default)s)',
                            metavar='SIZE',
                            type=argp.rangeCheck(float, 1, 49)))
    mmarg(pgrp.add_argument('--eventbox-title-color',
                            dest='eventboxTitleColor',
                            default='#000000',
                            help='color of the eventbox title '
                            '(default %(default)s)',
                            metavar='COLOR',
                            type=PIL.ImageColor.getrgb))

    pgrp = parser.add_argument_group('monthly calendar (m)',
                                     'Also see --event-file above.')
    pgrp.add_argument('--monthbox-firstweekday',
                      dest='monthboxFirstDay', default=0,
                      help='first day of week. 0 is Monday, 6 is Sunday '
                      '(default %(default)s)',
                      metavar='DAY',
                      type=argp.rangeCheck(int, 0, 6))
    pgrp.add_argument('--monthbox-dayoff',
                      dest='monthboxDayoff', default=[5, 6],
                      help='days off (marked as "red"). 0 is Monday, '
                      '6 is Sunday. Use e.g., -5 to unmark Saturday. '
                      '(default %(default)s)',
                      metavar='DAY', action='append',
                      type=argp.rangeCheck(int, -6, 6))

    mmarg(pgrp.add_argument('--monthbox-border-color',
                            dest='monthboxBorderColor',
                            default='#000000',
                            help='default border color around boxes '
                            '(default %(default)s)',
                            metavar='COLOR',
                            type=PIL.ImageColor.getrgb))

    mmarg(pgrp.add_argument('--monthbox-title-border-color',
                            dest='monthboxTitleBorderColor',
                            default='#FFFFFF',
                            help='border color around the title boxes '
                            '(default %(default)s)',
                            metavar='COLOR',
                            type=PIL.ImageColor.getrgb))

    colors = [
        ('title',      '#666666', '#FFFFFF', 'monthbox title (MON...)'),
        ('default',    '#666666', '#C2C2C2', 'default date'),
        ('today',      '#F3F3F3', '#598B94', 'today\'s date'),
        ('dayoff',     '#969696', '#C2C2C2', 'a day of'),
        ('othermonth', '#C8C5BE', '#F3F3F3', 'a day from other months'),
        ]

    for (key, c, bgc, desc) in colors:
        tkey = key.title()
        mmarg(pgrp.add_argument('--monthbox-%s-color' % key,
                                dest='monthbox%sColor' % tkey,
                                default=c,
                                help='text color of the %s '
                                '(default %%(default)s)' % desc,
                                metavar='COLOR',
                                type=PIL.ImageColor.getrgb))
        mmarg(pgrp.add_argument('--monthbox-%s-bgcolor' % key,
                                dest='monthbox%sBgColor' % tkey,
                                default=bgc,
                                help='background color of the %s '
                                '(default %%(default)s)' % desc,
                                metavar='COLOR',
                                type=PIL.ImageColor.getrgb))

    pgrp = parser.add_argument_group('simple date box (s)')
    mmarg(pgrp.add_argument('--simplebox-left', dest='simpleboxLeft',
                            default='%A',
                            help='datetext to show to the left '
                            '(default %(default)s)',
                            metavar='CONTENT'))
    mmarg(pgrp.add_argument('--simplebox-middle', dest='simpleboxMiddle',
                            default='%e',
                            help='datetext to show in the middle '
                            '(default %(default)s)',
                            metavar='CONTENT'))
    mmarg(pgrp.add_argument('--simplebox-right', dest='simpleboxRight',
                            default='%B',
                            help='datetext to show to the right '
                            '(default %(default)s)',
                            metavar='CONTENT'))
    mmarg(pgrp.add_argument('--simplebox-color', dest='simpleboxColor',
                            default='#000000',
                            help='color of the simplebox text '
                            '(default %(default)s)',
                            metavar='COLOR',
                            type=PIL.ImageColor.getrgb))

    args = parser.parse_args()

    try:
        # The file itself has already been opened
        args.image = pics.decorateImage(PIL.Image.open(args.imagefd))
    except IOError:
        log.error('main', '%r does not contain valid image data' %
                  args.imagefd.name)
        sys.exit(1)

    # use options depending on whether it's a landscape or portrait image
    argp.deMore(args, 0 if args.image.isLandscape() else 1)

    # Read contents of all events files
    evs = []
    for efd in (args.events or []):
        evs += events.readEventFile(efd)
    evs.sort()
    args.events = list(evs)

    # convert margins to pixels instead of %
    args.marginOuter = int(args.size[1] * args.marginOuter / 100.)
    args.marginInner = int(args.size[1] * args.marginInner / 100.)
    log.debug('main', 'Margins in pixels', args.marginInner, args.marginOuter)

    # Now check some of options
    log.VERBOSE = 2 if args.verbose else 1

    formatsp = r'(%s)' % '|'.join(boxes.getBoxTypes())
    formatsp = tuple(filter(None, re.split(formatsp, args.format[1])))
    args.format = args.format[0], formatsp

    # either --output or --show is required
    if not (args.outfn or args.show):
        log.info('main', '--output not used; assuming --show')
        args.show = True

    if args.outfn and args.skipIfExists:
        # check whether the file is already there
        try:
            img = PIL.Image.open(args.outfn)
            img.load()
            log.debug('main', args.outfn, 'found - not generating new version')
            if args.show:
                img.show()
            return
        except OSError:
            pass

    handle(args)


if __name__ == '__main__':
    main()
