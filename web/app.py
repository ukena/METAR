import subprocess
from flask import Flask, render_template, request
import yaml

app = Flask(__name__)

PI = True

@app.route("/", methods=["GET", "POST"])
def index():
    with open("/home/pi/config.yaml" if PI else "config.yaml") as f:
        config = yaml.safe_load(f)

    with open("/home/pi/config_default.yaml" if PI else "config_default.yaml") as f:
        standard = yaml.safe_load(f)

    if request.method == "POST":
        for key, data in request.form.items():
            if key in ("ssid", "passwort"):
                config["wlan"][key] = data
            elif key in ("vfr", "vfr_bei_wind", "mvfr", "mvfr_bei_wind", "ifr", "ifr_bei_wind", "lifr", "lifr_bei_wind", "blitze", "hoher_wind", "helligkeit"):
                config["farben"][key] = data
            elif key in ("normal", "hoch", "frequenz"):
                config["wind"][key] = data
            elif key in ("an", "aus"):
                config["zeiten"][key] = data
                # zeiten in crontab schreiben
                with open("/home/pi/karte/crontab" if PI else "karte/crontab", "w+") as f:
                    cron_an = f"*/5 {config['zeiten']['an']}-{int(config['zeiten']['aus']) - 1} * * *  /home/pi/karte/refresh.sh"
                    cron_aus = f"*/5 {config['zeiten']['aus']} * * *     /home/pi/karte/lightsoff.sh"
                    f.write(cron_an + "\n")
                    f.write(cron_aus + "\n")
                subprocess.call(["sudo", "crontab", "/home/pi/karte/crontab", "-"])
            elif key == "flugplaetze":
                config["flugplaetze"] = [i.strip() for i in data.split("\r")]
            elif key == "update-branch":
                if data in ("master", "dev"):
                    subprocess.Popen(["git", "fetch", "--all"], cwd="/home/pi")
                    subprocess.Popen(["git", "reset", "--hard", f"origin/{data}"], cwd="/home/pi")
                    subprocess.call(["sudo", "chmod", "+x", "/home/pi/handle_permissions.sh"])
                    subprocess.call(["sudo", "/home/pi/handle_permissions.sh"])

        # neue config parsen
        with open("/home/pi/config.yaml" if PI else "config.yaml", "w") as f:
            yaml.dump(config, f)

        # neue WLAN Einstellungen in wpa_supplicant.conf schreiben
        if PI:
            with open("/etc/wpa_supplicant/wpa_supplicant-wlan0.conf", "r") as f:
                in_file = f.readlines()
                f.close()

            out_file = []
            edited_psk = False
            edited_ssid = False
            for line in in_file:
                if "psk" in line and not edited_psk:
                    line = '    psk=' + '"' + config["wlan"]["passwort"] + '"' + '\n'
                    edited_psk = True
                elif "ssid" in line and not edited_ssid:
                    line = '    ssid=' + '"' + config["wlan"]["ssid"] + '"' + '\n'
                    edited_ssid = True
                out_file.append(line)

            with open("/etc/wpa_supplicant/wpa_supplicant-wlan0.conf", "w") as f:
                for line in out_file:
                    f.write(line)

            # neustart
            subprocess.call(["reboot"])

    return render_template("index.html", config=config, standard=standard)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
