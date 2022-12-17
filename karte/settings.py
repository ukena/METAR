from gpiozero import Button
import subprocess
from signal import pause
from git import Repo
from time import sleep

###TEST
# Button instanziieren
button = Button(23, hold_time=15)

# Funktion wird ausgeführt, wenn der Button 3 Sekunden gedrückt wird
def load_settings():
    # normales WLAN deaktivieren
    subprocess.call(["wpa_cli", "-i", "wlan0", "disable_network", "0"])
    # LEDs ausschalten
    subprocess.call(["sudo", "/home/metar/karte/lightsoff.sh"])
    sleep(1)
    # normales WLAN aktivieren (Verbindung aber erst nach dem Laden der Einstellungen)
    subprocess.call(["wpa_cli", "-i", "wlan0", "enable_network", "0"])

def reset_master():
    # repo auf den Stand des remote branches bringen
    repo = Repo("/home/metar")
    repo.remotes.origin.fetch()
    repo.git.reset("--hard")
    repo.git.checkout("master")
    repo.git.reset("--hard")
    repo.remotes.origin.pull()

    # Permissions updaten, damit cron funktioniert und alle Skripte ausführbar sind
    subprocess.call(["sudo", "chmod", "+x", "/home/metar/handle_permissions.sh"])
    subprocess.call(["sudo", "/home/metar/handle_permissions.sh"])

button.when_pressed = load_settings
button.when_held = reset_master

pause()