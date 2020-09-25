from PIL import Image
from generator import gen_frame, square_scale
import argparse
import os

parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter, description="""
GIF image combining utility""")

parser.add_argument("-i", "--input", help="\nPath to the source directory for the images", required=True, type=str)

args = parser.parse_args()

images = []

root = args.input

files = os.listdir(root)
files.sort()

for file in files:

    if file.endswith('.png'):

        src = Image.open(os.path.join(root, file))

        src = square_scale(src)

        src = gen_frame(src)
        images.append(src)

images[0].save(f'out.gif', save_all=True, disposal=2, append_images=images[1:],
               duration=70, loop=0)
