from gpiozero import Button
import subprocess
from signal import pause
import datetime

button = Button(23, hold_time=3)

def load_settings():
    with open("/etc/wpa_supplicant/wpa_supplicant-wlan0.conf", "r") as f:
        in_file = f.readlines()
        f.close()

    out_file = []
    edited_ssid = False
    for line in in_file:
        if "ssid" in line and not edited_ssid:
            line = '    ssid=' + '"823568923096753422238476835"' + '\n'
            edited_ssid = True
        out_file.append(line)

    with open("/etc/wpa_supplicant/wpa_supplicant-wlan0.conf", "w") as f:
        for line in out_file:
            f.write(line)

    with open("/home/pi/karte/settings-log-python.txt", "a") as g:
        g.write(f"Settings loaded at {datetime.datetime.now()}\n")

    subprocess.call(["/usr/bin/python3", "/home/pi/karte/pixelsoff.py"])
    subprocess.call(["sudo", "reboot"])

button.when_held = load_settings

pause()