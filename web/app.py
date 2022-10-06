import subprocess
from flask import Flask, render_template, request
import yaml
import logging
import git

app = Flask(__name__)

# zum debuggen, wenn lokal dann False, in Production True
PI = True
logging.basicConfig(filename='/home/pi/web/debug.log', encoding='utf-8', level=logging.DEBUG, force=True)

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
        # WLAN Konfiguration
        logging.debug(f"WLAN {request.form['ssid']} {request.form['passwort']}")
        config["wlan"]["ssid"] = request.form["ssid"]
        config["wlan"]["passwort"] = request.form["passwort"]
        # Version
        logging.debug(f"Version {request.form['version']}")
        config["version"] = request.form["version"]
        # Helligkeit
        logging.debug(f"Helligkeit {request.form['helligkeit']}")
        config["helligkeit"] = request.form["helligkeit"]
        # Farben Amerikanisch
        for key in ("vfr", "vfr_bei_wind", "mvfr", "mvfr_bei_wind", "ifr", "ifr_bei_wind", "lifr", "lifr_bei_wind", "blitze-amerikanisch", "hoher_wind"):
            config["farben_amerikanisch"][key] = request.form[key]
        # Farben GAFOR
        for key in ("charlie", "charlie_bei_wind", "oscar", "oscar_bei_wind", "delta", "delta_bei_wind", "mike", "mike_bei_wind", "xray", "xray_bei_wind", "blitze-gafor"):
            config["farben_gafor"][key] = request.form[key]
        # Wind
        config["wind"]["normal"] = request.form["normal"]
        config["wind"]["hoch"] = request.form["hoch"]
        config["wind"]["frequenz"] = request.form["frequenz"]
        # Zeiten
        config["zeiten"]["an"] = request.form["an"]
        config["zeiten"]["aus"] = request.form["aus"]
        config["zeiten"]["dauerbetrieb"] = request.form["dauerbetrieb"]
        # Flugplätze
        config["flugplaetze"] = [i.strip() for i in request.form["flugplaetze"].split("\r")]
        # Update
        if request.form["update-branch"] in ("master", "dev"):
            logging.debug(f"git reset auf branch {request.form['update-branch']}")
            # repo auf den Stand des remote branches bringen
            g = git.cmd.Git("/home/pi")
            g.fetch("--all")
            g.reset("--hard", f"origin/{request.form['update-branch']}")
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
                logging.debug(f"cronjob angepasst: {cron_an}")
            else:
                # Dauerbetrieb ist aus → Zeiten in crontab schreiben
                with open("/home/pi/karte/crontab", "w+") as f:
                    cron_an = f"*/5 {config['zeiten']['an']}-{int(config['zeiten']['aus']) - 1} * * *  /home/pi/karte/refresh.sh"
                    cron_aus = f"*/5 {config['zeiten']['aus']} * * *     /home/pi/karte/lightsoff.sh"
                    f.write(cron_an + "\n")
                    f.write(cron_aus + "\n")
                subprocess.call(["sudo", "crontab", "/home/pi/karte/crontab", "-"])
                logging.debug(f"cronjob angepasst: {cron_an} und {cron_aus}")

            # WLAN Einstellungen überarbeiten
            subprocess.call(["wpa_cli", "-i", "wlan0", "set_network", "0", "ssid", f'{config["wlan"]["ssid"]}'])
            subprocess.call(["wpa_cli", "-i", "wlan0", "set_network", "0", "psk", f'{config["wlan"]["passwort"]}'])

            # wieder mit dem normalen WLAN verbinden
            subprocess.call(["wpa_cli", "-i", "wlan0", "reconfigure"])
            logging.debug("wpa_cli ausgeführt")

    return render_template("index.html", config=config, standard=standard)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=True)
