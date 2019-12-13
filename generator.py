from PIL import Image, ImageChops
import numpy as np
import argparse
import os


def gen_frame(im):
    alpha = im.getchannel('A')
    im = im.convert('RGB').convert('P', palette=Image.ADAPTIVE, colors=255)
    mask = Image.eval(alpha, lambda a: 255 if a <= 128 else 0)
    im.paste(255, mask=mask)
    im.info['transparency'] = 255

    return im


def square_scale(im, scale=1, size=128):
    back = Image.new(mode='RGBA', size=(size, size), color=(0, 0, 0, 0))

    aspect = im.width/im.height

    if aspect >= 1:
        w = size
        h = size / aspect
    else:
        w = size * aspect
        h = size

    cpy = im.copy()
    cpy = cpy.resize((int(scale*w), int(scale*h)), resample=Image.ANTIALIAS)

    edge = int((1-scale) * size/2)

    back.paste(cpy, box=(edge, edge), mask=cpy)

    return back


def square_crop(im, x, y):
    back = Image.new(mode='RGBA', size=im.size, color=(0, 0, 0, 0))

    if abs(x) >= im.width or abs(y) >= im.height:
        return back

    box = (int(-x) if x < 0 else 0, int(-y) if y < 0 else 0,
           int(im.width - x) if x >= 0 else im.width, int(im.height - y) if y >= 0 else im.height)

    cpy = im.crop(box=box)

    back.paste(cpy, box=box, mask=cpy)

    return back


def make_gif(file, frames=12, fps=10, mode='bob', intensity=10, offset=0, size=128, crop=False):
    src = Image.open(file)

    modes = mode.split('-')
    intensities = str(intensity).split('-')
    offsets = str(offset).split('-')

    if len(modes) != len(intensities):
        if len(intensities) == 1:
            intensities = [intensities[0] for _ in modes]
        else:
            raise Exception("Supplied number of modes does not match number of intensity values")

    if len(modes) != len(offsets):
        if len(offsets) == 1:
            offsets = [offsets[0] for _ in modes]
        else:
            raise Exception("Supplied number of modes does not match number of offset values")

    images = []
    for f in range(frames):
        a = 0
        x = 0
        y = 0
        s = 1

        for n in range(len(modes)):
            m = modes[n]
            i = float(intensities[n])
            o = float(offsets[n])

            cos_factor = (1 - np.cos(2 * np.pi * f / frames)) / 2
            sin_factor = (np.sin(2 * np.pi * f / frames) + 1) / 2
            if m == 'spinccw':
                a += (360 / (frames-1)) * f + o
            if m in ['spin', 'spincw']:
                a -= (360 / (frames-1)) * f + o

            if m == 'right':
                x += (size / frames) * f + o if i != 0 else o
            if m == 'left':
                x -= (size / frames) * f + o if i != 0 else o
            if m == 'up':
                y -= (size / frames) * f + o if i != 0 else o
            if m == 'down':
                y += (size / frames) * f + o if i != 0 else o

            if m == 'bob':
                a += (sin_factor - 0.5) * 2 * i + o
            if m == 'shake':
                x += (cos_factor - 0.5) * 2 * i + o
            if m == 'bounce':
                y += (cos_factor - 0.5) * 2 * i + o

            if m == 'zoom':
                s = (1-cos_factor) + cos_factor * i + o
            if m == 'zoomout':
                s = (1-cos_factor) + cos_factor * i - o

        frame = src.copy()
        frame = square_scale(frame, scale=s, size=size)

        if crop:
            frame = square_crop(frame, x=x, y=y)
        frame = ImageChops.offset(frame.rotate(a), xoffset=int(x), yoffset=int(y))

        images.append(gen_frame(frame))

    filename = os.path.basename(file).replace('.png', '')
    images[0].save(f'gifs/very_{filename}.gif', save_all=True, disposal=2, append_images=images[1:],
                   duration=int(1000/fps), loop=0)


def parse_args():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter, description="""
    GIF generator utility""")

    parser.add_argument("-f", "--file", help="\nPath to the source image for the GIF", required=True, type=str)

    parser.add_argument("-m", "--mode", default='bob', type=str, help="""
Mode of animation. Supported types are:
-   [spin/spinccw]          Spins the image clockwise or counter-clockwise respectively.
-   [right/left/up/down]    Pans the image in the specified direction.
-   [bob]                   Oscillates the image rotation.
-   [shake/bounce]          Oscillates the image position side-to-side or up-and-down, respectively.

Combine multiple modes with a hyphen, e.g. --mode bob-shake-up. Default: bob.""")

    parser.add_argument("-v", "--fps", help="\nFramerate of GIF. Default: 10 FPS.", default=10, type=int)

    parser.add_argument("-n", "--frames", help="\nNumber of frames in GIF. Default: 12.", default=12, type=int)

    parser.add_argument("-i", "--intensity", default=10, type=str, help="""
Intensity of animation, depending on mode.
For rotational modes, supply angle in degrees.
For translational modes, supply a distance in pixels.
If there are multiple modes combined with hyphens, supply the same number of intensity values
separated by hyphens, e.g. "--mode bob-shake-up --intensity 20-10-0".
The spin and pan modes ignore intensity values. Default: 10""")

    parser.add_argument("-o", "--offset", default=0, type=str, help="""
Offset of animation, depending on mode.
For rotational modes, supply angle in degrees.
For translational modes, supply a distance in pixels. 
If there are multiple modes combined with hyphens, supply the same number of offset values
separated by hyphens, e.g. "--mode bob-shake-up --offset 20-10-0". Default: 10""")

    parser.add_argument("-c", "--crop", help="\nCrop off-screen images. By default, images tessellate",
                        action='store_true', default=False)

    parser.add_argument("-s", "--size", help="\nSize of GIF in pixels (will always be square). Default: 128.",
                        default=128, type=int)

    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()

    if not os.path.exists('gifs'):
        os.makedirs('gifs')

    if args.file.endswith('.png'):
        make_gif(args.file, frames=args.frames, fps=args.fps,
                 mode=args.mode, intensity=args.intensity, offset=args.offset, size=args.size, crop=args.crop)
    else:
        raise Exception("Please supply a PNG source file.")
