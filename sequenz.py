import board
import neopixel
import argparse
from time import sleep

def hex_to_grb(hex_color):
    hex_color = hex_color.replace("#", "")
    grb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return grb

def snake(color, rounds):
    for _ in range(rounds):
        for ind in range(0, 100):
            if ind not in skip:
                prev_prev_ind = min(ind - 2 if ind - 2 not in skip else ind - 3, 94)
                prev_ind = min(ind - 1 if ind - 1 not in skip else ind - 2, 94) if ind != 0 else 94
                next_ind = min(ind + 1 if ind + 1 not in skip else ind + 2, 94)

                pixels[prev_prev_ind] = hex_to_grb("#000000")
                pixels[prev_ind] = hex_to_grb(color)
                pixels[ind] = hex_to_grb(color)
                pixels[next_ind] = hex_to_grb(color)

                sleep(0.3)


if __name__ == "__main__":
    skip = [1, 23, 26, 31, 33, 95, 96, 97, 98, 99]
    pixels = neopixel.NeoPixel(board.D18, 100)
    parser = argparse.ArgumentParser()
    parser.add_argument("--modus", type=str, default="snake", choices=["snake", "error", "stop"])
    args = parser.parse_args()
    modus = args.modus

    if modus == "snake":
        snake(color="#ffffff", rounds=3)
    elif modus == "error":
        snake(color="#c90000", rounds=3)
    elif modus == "stop":
        pixels.deinit()
