from gpiozero import Button
import subprocess
from signal import pause
import datetime

# Button instanziieren
button = Button(23, hold_time=3)

# Funktion wird ausgeführt, wenn der Button 3 Sekunden gedrückt wird
def load_settings():
    # normales WLAN deaktivieren
    subprocess.call(["wpa_cli", "-i", "wlan0", "disable_network", "0"])
    # LEDs ausschalten
    subprocess.call(["/usr/bin/python3", "/home/pi/karte/pixelsoff.py"])
    # normales WLAN aktivieren (Verbindung aber erst nach dem Laden der Einstellungen)
    subprocess.call(["wpa_cli", "-i", "wlan0", "enable_network", "0"])

button.when_held = load_settings

pause()