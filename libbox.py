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
def today(args, f, image, box):
    image.drw.rectangle(box, (255, 40, 00), (0, 0, 255))


@boxType('c')
def calendar(args, f, image, box):
    image.drw.rectangle(box, (0, 255, 0), (0, 0, 255))
