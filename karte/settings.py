from gpiozero import Button
import subprocess
from signal import pause
from git import Repo
from time import sleep
import logging

logging.basicConfig(filename="settings-log-python.txt", encoding="utf-8", level=logging.DEBUG, force=True)
Button.was_held = False

def reset_master(btn):
    btn.was_held = True
    # LEDs ausschalten
    subprocess.call(["sudo", "/home/metar/karte/lightsoff.sh"])
    # repo auf den Stand des remote branches bringen
    i = 0
    repo = Repo("/home/metar")
    while i < 6:
        try:
            repo.remotes.origin.fetch()
            repo.git.reset("--hard")
            repo.git.checkout("master")
            repo.git.reset("--hard")
            repo.git.pull("origin", "master")
            i = 6
        except:
            sleep(10)
            i += 1

    # Permissions updaten, damit cron funktioniert und alle Skripte ausführbar sind
    subprocess.call(["sudo", "chmod", "+x", "/home/metar/handle_permissions.sh"])
    subprocess.call(["sudo", "/home/metar/handle_permissions.sh"])

def load_settings():
    logging.info("Button wurde gedrückt")
    # normales WLAN deaktivieren
    subprocess.call(["wpa_cli", "-i", "wlan0", "disable_network", "0"])
    # LEDs ausschalten
    subprocess.call(["sudo", "/home/metar/karte/lightsoff.sh"])
    sleep(1)
    # normales WLAN aktivieren (Verbindung aber erst nach dem Laden der Einstellungen)
    subprocess.call(["wpa_cli", "-i", "wlan0", "enable_network", "0"])

def released(btn):
    if not btn.was_held:
        logging.info("Button wurde gahalten")
        load_settings()
    btn.was_held = False

# Button instanziieren
button = Button(23, hold_time=15)
button.when_held = reset_master
button.when_released = released

pause()