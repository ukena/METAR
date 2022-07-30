import board
import neopixel

pixels = neopixel.NeoPixel(board.D18, 100)

pixels.deinit()

print("LEDs off")