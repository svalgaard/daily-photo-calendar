#
# Misc functions related to Pillow/pictures
#

import PIL.ImageDraw
from . import log

CENTER = object()


def resizeImageToFitInside(image, size):
    '''Resize a PIL image object to fit inside a box of size size'''
    f = list(float(size[i]) / image.size[i] for i in range(2))
    if max(f) < 1:
        # too large
        image.thumbnail(size, PIL.Image.ANTIALIAS)

    elif max(f) > 1:
        if f[0] > f[1]:
            newsize = (int(image.size[0] * f[1]), size[1])
        else:
            newsize = (size[0], int(image.size[1] * f[0]))
        image = image.resize(newsize)
    return image


def cropImage(image, size, rotationAllowed=False):
    '''Resize+crop a PIL Image object to exactly be of size size'''

    if rotationAllowed:
        if (size[0] > size[1]) != (image.size[0] > image.size[1]):
            size = size[::-1]

    w, h = image.size
    ws, hs = w*size[1], h*size[0]

    if ws <= hs:
        # too high
        # first make the width right
        nw, nh = size[0], 2*size[0]/image.size[0]*image.size[1]
        image = resizeImageToFitInside(image, (nw, nh))
        # delete at top and bottom
        nhs = (image.size[1]-size[1])//2
        nsize = (0, nhs, size[0], nhs+size[1])
        image = image.crop(nsize)
    elif ws > hs:
        # too wide
        # first make the height right
        nw, nh = 2*size[1]/image.size[1]*image.size[0], size[1]
        image = resizeImageToFitInside(image, (nw, nh))
        # delete at left and right
        nws = (image.size[0]-size[0])//2
        nsize = (nws, 0, nws+size[0], size[1])
        image = image.crop(nsize)

    return image


def decorateImage(image):
    if 'drw' not in dir(image):
        image.drw = PIL.ImageDraw.Draw(image)

        image.isLandscape = isLandscape.__get__(image, image.__class__)
        image.rotateCW = rotateCW.__get__(image, image.__class__)
        image.rotateCCW = rotateCCW.__get__(image, image.__class__)

    return image


def isLandscape(image):
    return image.size[0] >= image.size[1]


def rotateCW(image):
    res = image.transpose(PIL.Image.ROTATE_270)
    res = decorateImage(res)

    if 'box' in dir(image):
        # also rotate the box
        box = image.box
        res.box = (image.size[1] - box[3], box[0],
                   image.size[1] - box[1], box[2])

    return decorateImage(res)


def rotateCCW(image):
    res = image.transpose(PIL.Image.ROTATE_90)
    res = decorateImage(res)

    if 'box' in dir(image):
        # also rotate the box
        box = image.box
        res.box = (box[1], image.size[0] - box[2],
                   box[3], image.size[0] - box[0])

    return decorateImage(res)


def textDraw(image, box, text, color, font, position=CENTER, squeezed=False):
    global CENTER
    decorateImage(image)

    boxsize = (box[2] - box[0], box[3] - box[1])
    if squeezed:
        mask, offset = font.getmask2(text)
        textsize = mask.size
    else:
        textsize = image.drw.textsize(text, font)

    if type(position) not in (tuple, list):
        pos = [position, position]
    else:
        pos = list(position)
    assert(len(pos) == 2)

    for i in range(2):
        if pos[i] is CENTER:
            pos[i] = box[i] + (boxsize[i]-textsize[i])/2
        elif pos[i] < 0:
            pos[i] = box[i] + boxsize[i] + pos[i] - textsize[i]
        else:
            pos[i] = box[i]+pos[i]  # go from relative to absolute
    if squeezed:
        pos[0] -= offset[0]
        pos[1] -= offset[1]

    image.drw.text(pos, text, font=font, fill=color)


def scaleFont(font, newSize):
    dlfn = font if type(font) == str else font.path
    font = PIL.ImageFont.truetype(dlfn, newSize)
    # font.dlfn = dlfn
    # font.dsize = newSize
    return font


def intBox(box):
    return tuple(int(b+.5) for b in box)


def fitFontSize(font, text, box, squeezed=False):
    '''Find largest font where text can be fitted within the box'''
    if len(box) == 2:
        w, h = box
    else:
        w, h = box[2] - box[0], box[3] - box[1]

    size = 2*h
    while size > 1:
        font = scaleFont(font, size)
        if squeezed:
            textsize = font.getmask(text).size
        else:
            textsize = font.getsize(text)
        # log.debug('fitFontSize', '==', textsize, 'for fontsize=', font.dsize)
        if textsize[0] <= w and textsize[1] <= h:
            break
        size -= 1
    log.debug('fitFontSize', 'Scaling', text, 'into', textsize,
              '<=', (w, h),
              'font.size=', font.size)
    return font
