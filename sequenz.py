import board
import neopixel
from time import sleep

colors = ['#ffffff', '#ffff00', '#ff0000', '#7d0000', '#7d007d', '#4b004b', '#0000ff', '#00007d', '#00ff00', '#007d00',
          '#00ADEF', '#005577', '#FEF200', '#7f7800', '#F7921C', '#7b490e', '#4EB849', '#275c24', '#ED1B24', '#760d12']
skip = [1, 23, 26, 31, 33]
pixels = neopixel.NeoPixel(board.D18, 100)

def hex_to_grb(hex_color):
    hex_color = hex_color.replace("#", "")
    grb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return grb

def fade():
    for ind, _ in enumerate(pixels):
        if ind not in skip:
            prev_ind = pixels[ind - 1] if ind - 1 not in skip else pixels[ind - 2]
            next_ind = pixels[ind + 1] if ind + 1 not in skip else pixels[ind + 2]


            pixels[prev_ind].fill((hex_to_grb("#7f7f7f")))
            pixels[ind].fill((hex_to_grb("#ffffff")))
            pixels[next_ind].fill((hex_to_grb("#7f7f7f")))
            sleep(0.3)


try:
    while True:
        fade()
except:
    pixels.deinit()