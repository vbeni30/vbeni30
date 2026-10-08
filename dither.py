"""Turn any photo into the dithered pixel style used in the README.
Usage: python dither.py photo.jpg assets/about.png
Needs: pip install pillow numpy"""
import sys, numpy as np
from PIL import Image, ImageOps

src, out = sys.argv[1], sys.argv[2]
BG, FG, SCALE, SIZE = (13, 17, 23), (230, 237, 243), 4, 120
img = ImageOps.autocontrast(ImageOps.fit(Image.open(src).convert("L"), (SIZE, SIZE)), cutoff=2)
lum = np.array(img) / 255.0
bayer = np.array([[0,32,8,40,2,34,10,42],[48,16,56,24,50,18,58,26],[12,44,4,36,14,46,6,38],[60,28,52,20,62,30,54,22],
                  [3,35,11,43,1,33,9,41],[51,19,59,27,49,17,57,25],[15,47,7,39,13,45,5,37],[63,31,55,23,61,29,53,21]]) / 64
t = np.tile(bayer, (SIZE // 8 + 1, SIZE // 8 + 1))[:SIZE, :SIZE]
px = np.zeros((SIZE, SIZE, 3), np.uint8); px[:] = BG; px[lum > t] = FG
Image.fromarray(px).resize((SIZE * SCALE,) * 2, Image.NEAREST).save(out)
