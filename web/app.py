import subprocess
from flask import Flask, render_template, request
import yaml

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    with open("config.yaml") as f:
        config = yaml.safe_load(f)

    if request.method == "POST":
        for key, data in request.form.items():
            if key in ("ssid", "passwort"):
                config["wlan"][key] = data
            elif key in ("vfr", "vfr_bei_wind", "mvfr", "mvfr_bei_wind", "ifr", "ifr_bei_wind", "lifr", "lifr_bei_wind", "blitze", "hoher_wind"):
                config["farben"][key] = data
            elif key in ("normal", "hoch", "frequenz"):
                config["wind"][key] = data
            elif key in ("an", "aus"):
                config["zeiten"][key] = data
            elif key == "update-branch":
                if data in ("master", "dev"):
                    subprocess.call(["git", "fetch", "--all"])
                    subprocess.call(["git", "reset", "--hard", f"origin/{data}"])

        with open("config.yaml", "w") as f:
            yaml.dump(config, f)

        # neue WLAN Einstellungen in wpa_supplicant.conf schreiben
        with open("/etc/wpa_supplicant/wpa_supplicant-wlan0.conf", "r") as f:
            in_file = f.readlines()
            f.close()

        out_file = []
        edited_psk = False
        edited_ssid = False
        for line in in_file:
            if line.startswith("psk") and not edited_psk:
                line = 'psk=' + '"' + config["wlan"]["passwort"] + '"' + '\n'
                edited_psk = True
            elif line.startswith("ssid") and not edited_ssid:
                line = 'ssid=' + '"' + config["wlan"]["ssid"] + '"' + '\n'
                edited_ssid = True
            out_file.append(line)

        with open("/etc/wpa_supplicant/wpa_supplicant-wlan0.conf", "w") as f:
            for line in out_file:
                f.write(line)

        # neustart
        # subprocess.call(["reboot", "-h", "now"])

    return render_template("index.html", config=config)


if __name__ == "__main__":
    app.run()
