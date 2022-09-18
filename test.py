import board
import neopixel
from time import sleep

COLORS = ['#ffffff', '#ffff00', '#ff0000', '#7d0000', '#7d007d', '#4b004b', '#0000ff', '#00007d', '#00ff00', '#007d00',
          '#00ADEF', '#005577', '#FEF200', '#7f7800', '#F7921C', '#7b490e', '#4EB849', '#275c24', '#ED1B24', '#760d12']

def hex_to_grb(hex_color):
    hex_color = hex_color.replace("#", "")
    grb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return grb

pixels = neopixel.NeoPixel(board.D18, 100)

try:
    while True:
        for color in COLORS:
            pixels.fill((hex_to_grb(color)))
            sleep(1)
except:
    pixels.deinit()