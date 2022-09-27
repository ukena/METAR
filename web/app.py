import subprocess
from flask import Flask, render_template, request
import yaml

app = Flask(__name__)

# zum debuggen, wenn lokal dann False, in Production True
PI = False

@app.route("/", methods=["GET", "POST"])
def index():
    # aktuelle Konfiguration auslesen
    with open("/home/pi/config.yaml" if PI else "config.yaml") as f:
        config = yaml.safe_load(f)
    # Standardeinstellungen auslesen
    with open("/home/pi/config_default.yaml" if PI else "config_default.yaml") as f:
        standard = yaml.safe_load(f)

    # wenn Formular abgeschickt wurde
    if request.method == "POST":
        # über alle Formularfelder iterieren und die Werte in die aktuelle Konfiguration schreiben
        for key, data in request.form.items():
            if key in ("ssid", "passwort"):
                config["wlan"][key] = data
            elif key == "version":
                config["version"] = data
            elif key == "helligkeit":
                config["helligkeit"] = data
            elif key in ("vfr", "vfr_bei_wind", "mvfr", "mvfr_bei_wind", "ifr", "ifr_bei_wind", "lifr", "lifr_bei_wind", "blitze-amerikanisch", "hoher_wind"):
                config["farben_amerikanisch"][key] = data
            elif key in ("charlie", "charlie_bei_wind", "oscar", "oscar_bei_wind", "delta", "delta_bei_wind", "mike", "mike_bei_wind", "xray", "xray_bei_wind", "blitze-gafor"):
                config["farben_gafor"][key] = data
            elif key in ("normal", "hoch", "frequenz"):
                config["wind"][key] = data
            elif key in ("an", "aus", "dauerbetrieb"):
                config["zeiten"][key] = data
            elif key == "flugplaetze":
                config["flugplaetze"] = [i.strip() for i in data.split("\r")]
            elif key == "update-branch":
                if data in ("master", "dev"):
                    # repo auf den Stand des remote branches bringen
                    subprocess.Popen(["git", "fetch", "--all"], cwd="/home/pi")
                    subprocess.Popen(["git", "reset", "--hard", f"origin/{data}"], cwd="/home/pi")
                    # Permissions updaten, damit cron funktioniert und alle Skripte ausführbar sind
                    subprocess.call(["sudo", "chmod", "+x", "/home/pi/handle_permissions.sh"])
                    subprocess.call(["sudo", "/home/pi/handle_permissions.sh"])

        # neue config parsen
        with open("/home/pi/config.yaml" if PI else "config.yaml", "w") as f:
            yaml.dump(config, f)

        if PI:
            if config["zeiten"]["dauerbetrieb"] == "on":
                # Dauerbetrieb ist aktiv → cronjob anpassen, damit lightsoff.sh nicht ausgeführt wird
                with open("/home/pi/karte/crontab", "w+") as f:
                    cron_an = "*/5 * * * *  /home/pi/karte/refresh.sh"
                    f.write(cron_an + "\n")
                subprocess.call(["sudo", "crontab", "/home/pi/karte/crontab", "-"])
            else:
                # Dauerbetrieb ist aus → Zeiten in crontab schreiben
                with open("/home/pi/karte/crontab", "w+") as f:
                    cron_an = f"*/5 {config['zeiten']['an']}-{int(config['zeiten']['aus']) - 1} * * *  /home/pi/karte/refresh.sh"
                    cron_aus = f"*/5 {config['zeiten']['aus']} * * *     /home/pi/karte/lightsoff.sh"
                    f.write(cron_an + "\n")
                    f.write(cron_aus + "\n")
                subprocess.call(["sudo", "crontab", "/home/pi/karte/crontab", "-"])

            # WLAN Einstellungen überarbeiten
            subprocess.call(["wpa_cli", "-i", "wlan0", "set_network ", "0", "ssid", config["wlan"]["ssid"]])
            subprocess.call(["wpa_cli", "-i", "wlan0", "set_network ", "0", "psk", config["wlan"]["passwort"]])

            # wieder mit dem normalen WLAN verbinden
            subprocess.call(["wpa_cli", "-i", "wlan0", "reconfigure"])

    return render_template("index.html", config=config, standard=standard)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
