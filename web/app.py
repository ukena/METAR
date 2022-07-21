from flask import Flask, render_template, request
import yaml

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    with open("config.yaml") as f:
        config = yaml.safe_load(f)

    if request.method == "POST":
        print(request.form)
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
                if data == "main":
                    # subprocess.call(["git", "checkout", "main"])
                    # subprocess.call(["git", "pull", "origin", "main"])
                    pass
                elif data == "dev":
                    # subprocess.call(["git", "checkout", "dev"])
                    # subprocess.call(["git", "pull", "origin", "dev"])
                    pass
        with open("config.yaml", "w") as f:
            yaml.dump(config, f)
        # TODO: write wifi setting into wpa_supplicant.conf, reboot


    return render_template("index.html", config=config)


if __name__ == '__main__':
    app.run()
