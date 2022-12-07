import subprocess
from flask import Flask, render_template, request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, BooleanField, RadioField, TextAreaField, SelectField, DecimalRangeField
from wtforms.widgets.core import ColorInput
from wtforms.validators import DataRequired, Length, NumberRange
import yaml
import logging
import git

app = Flask(__name__)
app.config["SECRET_KEY"] = "GFvKeDNdZ5HVD93CRLWUHZya3f63tFKO"

# zum debuggen, wenn lokal dann False, in Production True
PI = False
logging.basicConfig(filename="/home/metar/web/debug.log" if PI else "debug.log", encoding="utf-8", level=logging.DEBUG, force=True)

FARBEN_AMERIKANISCH = ("vfr", "vfr_bei_wind", "mvfr", "mvfr_bei_wind", "ifr", "ifr_bei_wind", "lifr", "lifr_bei_wind", "blitze-amerikanisch", "hoher_wind")
FARBEN_GAFOR = ("charlie", "charlie_bei_wind", "oscar", "oscar_bei_wind", "delta", "delta_bei_wind", "mike", "mike_bei_wind", "xray", "xray_bei_wind", "blitze-gafor")

class Einstellungen(FlaskForm):
    style = {"class": "form-control"}

    form_ssid = StringField("Name (z.B. FRITZ!Box 7590 TN)", validators=[DataRequired(), Length(min=1, max=128)], render_kw=style)
    form_passwort = PasswordField("Passwort", validators=[DataRequired(), Length(min=1, max=256)], render_kw=style)
    form_version = RadioField("Version", validators=[DataRequired()], choices=[("amerikanisch", "Amerikanisch"), ("gafor", "GAFOR")], default="gafor")

    for farbe in FARBEN_AMERIKANISCH:
        locals()["form_" + farbe] = StringField(farbe.replace("_", " "), widget=ColorInput(), validators=[DataRequired()], render_kw=style)
    for farbe in FARBEN_GAFOR:
        locals()["form_" + farbe] = StringField(farbe.replace("_", " "), widget=ColorInput(), validators=[DataRequired()], render_kw=style)

    form_helligkeit = DecimalRangeField("Helligkeit", validators=[DataRequired()], default=0.5, render_kw=style)

    form_normal = StringField("normal", validators=[DataRequired(), NumberRange(1, 15)], render_kw=style)
    form_hoch = StringField("hoch", validators=[DataRequired()], render_kw=style)
    form_frequenz = StringField("Frequenz", validators=[DataRequired()], render_kw=style)

    form_an = StringField("an", validators=[DataRequired()], render_kw=style)
    form_aus = StringField("aus", validators=[DataRequired()], render_kw=style)
    form_dauerbetrieb = BooleanField("Dauerbetrieb", validators=[DataRequired()])

    form_flugplaetze = TextAreaField("Flugplätze", validators=[DataRequired()], render_kw=style)

    form_update = SelectField("Update", choices=[("kein update", "kein update"), ("master", "master"), ("dev", "dev")], default="kein update", render_kw=style)

    submit = SubmitField("Speichern")

@app.route("/", methods=["GET", "POST"])
def index():
    # aktuelle Konfiguration auslesen
    with open("/home/metar/config.yaml" if PI else "config.yaml") as f:
        config = yaml.safe_load(f)
    # Standardeinstellungen auslesen
    with open("/home/metar/config_default.yaml" if PI else "config_default.yaml") as f:
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
        for key in FARBEN_AMERIKANISCH:
            config["farben_amerikanisch"][key] = request.form[key]
        # Farben GAFOR
        for key in FARBEN_GAFOR:
            config["farben_gafor"][key] = request.form[key]
        # Wind
        config["wind"]["normal"] = request.form.get("normal", "15")
        config["wind"]["hoch"] = request.form.get("hoch", "25")
        config["wind"]["frequenz"] = request.form.get("frequenz", "1")
        # Zeiten
        config["zeiten"]["an"] = request.form.get("an", "8")
        config["zeiten"]["aus"] = request.form.get("aus", "22")
        config["zeiten"]["dauerbetrieb"] = request.form.get("dauerbetrieb", False)
        # Flugplätze
        config["flugplaetze"] = [i.strip() for i in request.form["flugplaetze"].split("\r")]
        # Update
        if request.form["update-branch"] in ("master", "dev"):
            logging.debug(f"git reset auf branch {request.form['update-branch']}")
            # repo auf den Stand des remote branches bringen
            g = git.cmd.Git("/home/metar")
            g.fetch("--all")
            g.reset("--hard", f"origin/{request.form['update-branch']}")
            # Permissions updaten, damit cron funktioniert und alle Skripte ausführbar sind
            subprocess.call(["sudo", "chmod", "+x", "/home/metar/handle_permissions.sh"])
            subprocess.call(["sudo", "/home/metar/handle_permissions.sh"])

        # neue config parsen
        with open("/home/metar/config.yaml" if PI else "config.yaml", "w") as f:
            yaml.dump(config, f)

        if PI:
            if config["zeiten"]["dauerbetrieb"]:
                # Dauerbetrieb ist aktiv → cronjob anpassen, damit lightsoff.sh nicht ausgeführt wird
                with open("/home/metar/karte/crontab", "w+") as f:
                    cron_an = "*/5 * * * *  /home/metar/karte/refresh.sh"
                    f.write(cron_an + "\n")
                subprocess.call(["sudo", "crontab", "/home/metar/karte/crontab", "-"])
                logging.debug(f"cronjob angepasst: {cron_an}")
            else:
                # Dauerbetrieb ist aus → Zeiten in crontab schreiben
                with open("/home/metar/karte/crontab", "w+") as f:
                    cron_an = f"*/5 {config['zeiten']['an']}-{int(config['zeiten']['aus']) - 1} * * *  /home/metar/karte/refresh.sh"
                    cron_aus = f"*/5 {config['zeiten']['aus']} * * *     /home/metar/karte/lightsoff.sh"
                    f.write(cron_an + "\n")
                    f.write(cron_aus + "\n")
                subprocess.call(["sudo", "crontab", "/home/metar/karte/crontab", "-"])
                logging.debug(f"cronjob angepasst: {cron_an} und {cron_aus}")

            # WLAN Einstellungen überarbeiten
            subprocess.call(["wpa_cli", "-i", "wlan0", "set_network", "0", "ssid", f'{config["wlan"]["ssid"]}'])
            subprocess.call(["wpa_cli", "-i", "wlan0", "set_network", "0", "psk", f'{config["wlan"]["passwort"]}'])

            # wieder mit dem normalen WLAN verbinden
            subprocess.call(["wpa_cli", "-i", "wlan0", "reconfigure"])
            logging.debug("wpa_cli ausgeführt")

    # Einstellungsformular instanziieren
    form = Einstellungen()
    # WLAN Daten ausfüllen
    form.form_ssid.data = config["wlan"]["ssid"]
    form.form_passwort.data = config["wlan"]["passwort"]
    # Version ausfüllen
    form.form_version.data = config["version"]
    # GAFOR Farben ausfüllen
    for farbe in FARBEN_GAFOR:
        form["form_" + farbe].data = config["farben_gafor"][farbe]
    # Amerikanische Farben ausfüllen
    for farbe in FARBEN_AMERIKANISCH:
        form["form_" + farbe].data = config["farben_amerikanisch"][farbe]
    # Wind ausfüllen
    form.form_normal.data = config["wind"]["normal"]
    form.form_hoch.data = config["wind"]["hoch"]
    form.form_frequenz.data = config["wind"]["frequenz"]
    # Zeiten ausfüllen
    form.form_an.data = config["zeiten"]["an"]
    form.form_aus.data = config["zeiten"]["aus"]
    form.form_dauerbetrieb.data = config["zeiten"]["dauerbetrieb"]
    # Flugplätze ausfüllen
    form.form_flugplaetze.data = "\r".join(config["flugplaetze"])

    return render_template("index.html", config=config, standard=standard, form=form, FARBEN_AMERIKANISCH=FARBEN_AMERIKANISCH, FARBEN_GAFOR=FARBEN_GAFOR)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=True)
