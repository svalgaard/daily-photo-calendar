#
# Misc functions related to Pillow/pictures
#

import PIL.ImageDraw

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

        def isLandscape():
            return image.size[0] >= image.size[1]
        image.isLandscape = isLandscape
    return image


def textDraw(image, box, text, color, font, position=CENTER):
    global CENTER
    decorateImage(image)

    boxsize = (box[2] - box[0], box[3] - box[1])
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

    image.drw.text(pos, text, font=font, fill=color)


def scaleFont(font, newSize):
    dlfn = font if type(font) == str else font.dlfn
    font = PIL.ImageFont.truetype(dlfn, newSize)
    font.dlfn = dlfn
    font.dsize = newSize
    return font


def intBox(box):
    return tuple(int(b+.5) for b in box)
