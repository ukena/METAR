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
    logging.info("Button wurde gahalten")
    # LEDs ausschalten
    subprocess.call(["sudo", "/home/metar/karte/lightsoff.sh"])
    # reset sequenz starten
    subprocess.call(["sudo", "python", "/home/metar/karte/sequenz.py", "--modus", "snake"])

    # repo auf den Stand des lokalen reset branches bringen
    repo = Repo("/home/metar")
    repo.git.checkout("master")
    repo.git.reset("--hard", "reset")

    # Permissions updaten, damit cron funktioniert und alle Skripte ausführbar sind
    subprocess.call(["sudo", "chmod", "+x", "/home/metar/handle_permissions.sh"])
    subprocess.call(["sudo", "/home/metar/handle_permissions.sh"])

def load_settings():
    logging.info("Button wurde gedrückt")
    # normales WLAN deaktivieren
    subprocess.call(["wpa_cli", "-i", "wlan0", "disable_network", "0"])
    # LEDs ausschalten
    subprocess.call(["sudo", "/home/metar/karte/lightsoff.sh"])
    # reset sequenz starten
    subprocess.call(["sudo", "python", "/home/metar/karte/sequenz.py", "--modus", "snake"])
    # normales WLAN aktivieren (Verbindung aber erst nach dem Laden der Einstellungen)
    subprocess.call(["wpa_cli", "-i", "wlan0", "enable_network", "0"])

def released(btn):
    if not btn.was_held:
        load_settings()
    btn.was_held = False

# Button instanziieren
button = Button(23, hold_time=10, bounce_time=0.2)
button.when_held = reset_master
button.when_released = released

pause()