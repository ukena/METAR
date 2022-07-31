import board
import neopixel
from time import sleep

pixels = neopixel.NeoPixel(board.D18, 100)
SLEEP = .5

try:
    while True:
        pixels.fill((0,255,0))    # red
        sleep(SLEEP)
        pixels.fill((255,0,0))    # green
        sleep(SLEEP)
        pixels.fill((0,0,255))    # blue
        sleep(SLEEP)
        pixels.fill((0,125,125))  # purple
        sleep(SLEEP)
except:
    pixels.deinit()