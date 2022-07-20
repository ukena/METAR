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
            elif key in ("vfr", "vfr_bei_wind", "mvfr", "mvfr_bei_wind", "ifr", "ifr_bei_wind", "lifr", "lifr_bei_wind", "blitze", "sturm"):
                config["farben"][key] = data
            elif key in ("normal", "hoch", "frequenz"):
                config["wind"][key] = data
            elif key in ("an", "aus"):
                config["zeiten"][key] = data
        with open("config.yaml", "w") as f:
            yaml.dump(config, f)
        # TODO: stop AP, start WLAN, connect

    return render_template("index.html", config=config)


if __name__ == '__main__':
    app.run()
