import RPi.GPIO as GPIO
import subprocess
import time

GPIO.setmode(GPIO.BCM)
GPIO.setup(23, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def load_settings(channel):
    with open("/etc/wpa_supplicant/wpa_supplicant-wlan0.conf", "r") as f:
        in_file = f.readlines()
        f.close()

    out_file = []
    edited_ssid = False
    for line in in_file:
        if "ssid" in line and not edited_ssid:
            line = '    ssid=' + '"123456789101112"' + '\n'
            edited_ssid = True
        out_file.append(line)

    with open("/etc/wpa_supplicant/wpa_supplicant-wlan0.conf", "w") as f:
        for line in out_file:
            f.write(line)

    subprocess.call(["/usr/bin/python3", "/home/pi/karte/pixelsoff.py"])
    subprocess.call(["sudo", "reboot"])

GPIO.add_event_detect(23, GPIO.FALLING, callback=load_settings, bouncetime=500)

while 1:
    time.sleep(0.1)