import os
import subprocess
from flask import Flask, render_template, request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField, RadioField, TextAreaField, SelectField, DecimalRangeField, IntegerField
from wtforms.widgets.core import ColorInput
from wtforms.validators import InputRequired, NumberRange, AnyOf, ValidationError, EqualTo
from wtforms.widgets import PasswordInput
import yaml
import logging
from git import Repo
from time import sleep

app = Flask(__name__)
app.config["SECRET_KEY"] = "GFvKeDNdZ5HVD93CRLWUHZya3f63tFKO"

# zum debuggen, wenn lokal dann False, in Production True
PI = True
BASE_DIR = "/home/metar" if PI else os.getcwd()
logging.basicConfig(filename=f"{BASE_DIR}/web/debug.log" if PI else "debug.log", encoding="utf-8", level=logging.DEBUG, force=True)

FARBEN_AMERIKANISCH = ("vfr", "vfr_bei_wind", "mvfr", "mvfr_bei_wind", "ifr", "ifr_bei_wind", "lifr", "lifr_bei_wind", "blitze-amerikanisch", "hoher_wind")
FARBEN_GAFOR = ("charlie", "charlie_bei_wind", "oscar", "oscar_bei_wind", "delta", "delta_bei_wind", "mike", "mike_bei_wind", "xray", "xray_bei_wind", "blitze-gafor")


class KleinerAls(object):
    def __init__(self, anderes_feld, message, versionscheck=False):
        self.anderes_feld = anderes_feld
        self.message = message
        self.versionscheck = versionscheck

    def __call__(self, form, eigenes_feld):

        anderes_feld = form[self.anderes_feld]

        # Wenn die Version GAFOR ist, dann ist es egal, ob der Wind kleiner als der hohe Wind ist, weil es sowieso nur eine Windanzeige gibt
        if self.versionscheck and form["form_version"].data == "gafor" and anderes_feld.data < eigenes_feld.data:
            print(f"mit version {form['form_version'].data}")
            pass
        elif anderes_feld.data < eigenes_feld.data:
            raise ValidationError(self.message)


kleiner_als = KleinerAls


class Einstellungen(FlaskForm):
    class Meta:
        csrf = False

    style = {"class": "form-control"}

    form_ssid = StringField("Name (z.B. FRITZ!Box 7590 TN)", validators=[InputRequired(message="Es wird zwingend der WLAN Name benötigt.")], render_kw=style)
    form_passwort = StringField("Passwort", widget=PasswordInput(hide_value=False), validators=[InputRequired(message="Es wird zwingend ein WLAN Passwort benötigt.")], render_kw=style)
    form_version = SelectField("Version", validators=[InputRequired(message="Die Version Deiner Karte muss \"Amerikanisch\" oder \"GAFOR\" sein.")], choices=[("amerikanisch", "Amerikanisch"), ("gafor", "GAFOR")], render_kw=style)

    for farbe in FARBEN_AMERIKANISCH:
        locals()["form_" + farbe] = StringField(farbe.replace("_", " ").replace("-amerikanisch", ""), widget=ColorInput(), validators=[InputRequired(message=f'Die Farbe für {farbe.replace("_", " ").replace("-amerikanisch", "")} fehlt.')], render_kw=style)
    for farbe in FARBEN_GAFOR:
        locals()["form_" + farbe] = StringField(farbe.replace("_", " ").replace("-gafor", ""), widget=ColorInput(), validators=[InputRequired(message=f'Die Farbe für {farbe.replace("_", " ").replace("-amerikanisch", "")} fehlt.')], render_kw=style)

    form_helligkeit = DecimalRangeField("Helligkeit", validators=[InputRequired(message="Ein Wert für die Helligkeit muss angegeben werden."),
                                                                  NumberRange(min=0.1, max=1, message="Die Helligkeit muss zwischen 0,1 und 1 liegen.")], default=0.5, render_kw=style)

    form_normal = IntegerField("Wind", validators=[InputRequired(message="Die Windgeschwindigkeit muss angegeben werden."),
                                                   NumberRange(min=1, max=60, message="Die Windgeschwindigkeit muss zwischen 1 und 60 Knoten liegen."),
                                                   kleiner_als("form_hoch", versionscheck=True, message="Die Windgeschwindigkeit zum Anzeigen von Wind muss kleiner sein als die von hohen Wind.")], render_kw=style)
    form_hoch = IntegerField("Hoher Wind", validators=[InputRequired(message="Die Windgeschwindigkeit für hohen Wind muss angegeben werden."),
                                                       NumberRange(min=1, max=60, message="Die Windgeschwindigkeit muss zwischen 1 und 60 Knoten liegen.")], render_kw=style)
    form_frequenz = IntegerField("Frequenz", validators=[InputRequired(message="Die Frequenz des Blinkens muss angegeben werden."),
                                                         NumberRange(min=1, max=30, message="Die Frequenz des Blinkens muss zwischen 1 und 30 Sekunden liegen.")], render_kw=style)

    form_an = IntegerField("Einschalten", validators=[InputRequired(message="Selbst wenn der Dauerbetrieb aktiv ist muss eine Zeit zum Einschalten gegeben werden."),
                                                      NumberRange(min=0, max=24),
                                                      kleiner_als("form_aus", message="Die Uhrzeit zum Einschalten muss kleiner sein als die zum Ausschalten.")], render_kw=style)
    form_aus = IntegerField("Ausschalten", validators=[InputRequired(message="Selbst wenn der Dauerbetrieb aktiv ist muss eine Zeit zum Ausschalten gegeben werden."),
                                                       NumberRange(min=0, max=24)], render_kw=style)
    form_dauerbetrieb = BooleanField("Dauerbetrieb")

    form_flugplaetze = TextAreaField("Flugplätze", validators=[InputRequired(message="Die Liste der Flugplätze kann nicht leer sein.")], render_kw=style)

    form_update = SelectField("Update", validators=[InputRequired(message="Es muss angegeben werden, ob ein update gewünscht ist und wenn ja aus welcher Quelle.")], choices=[("kein update", "kein update"), ("main", "main"), ("dev", "dev"), ("hotfix", "hotfix")], default="kein update", render_kw=style)

    submit = SubmitField("Speichern")

@app.route("/", methods=["GET", "POST"])
def index():
    # aktuelle Konfiguration auslesen
    with open(f"{BASE_DIR}/config.yaml" if PI else "config.yaml") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    # Standardeinstellungen auslesen
    with open(f"{BASE_DIR}/config_default.yaml" if PI else "config_default.yaml") as f:
        standard = yaml.load(f, Loader=yaml.FullLoader)

    # Einstellungsformular instanziieren
    form = Einstellungen()

    # nur beim ersten Laden der Seite ausführen, sonst werden Formulardaten bei jedem invaliden submit überschrieben
    if not form.is_submitted():
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
        # Helligkeit ausfüllen
        form.form_helligkeit.data = float(config["helligkeit"])
        # Wind ausfüllen
        form.form_normal.data = int(config["wind"]["normal"])
        form.form_hoch.data = int(config["wind"]["hoch"])
        form.form_frequenz.data = int(config["wind"]["frequenz"])
        # Zeiten ausfüllen
        form.form_an.data = int(config["zeiten"]["an"])
        form.form_aus.data = int(config["zeiten"]["aus"])
        form.form_dauerbetrieb.checked = True if config["zeiten"]["dauerbetrieb"] == "true" else False
        # Flugplätze ausfüllen
        form.form_flugplaetze.data = "\r".join(config["flugplaetze"])

    # wenn Formular abgeschickt wurde
    # if request.method == "POST":
    if form.validate_on_submit():
        # WLAN Konfiguration
        logging.debug(f"WLAN {request.form['form_ssid']} {request.form['form_passwort']}")
        config["wlan"]["ssid"] = request.form["form_ssid"]
        config["wlan"]["passwort"] = request.form["form_passwort"]
        # Version
        logging.debug(f"Version {request.form['form_version']}")
        config["version"] = request.form["form_version"]
        # Helligkeit
        logging.debug(f"Helligkeit {request.form['form_helligkeit']}")
        config["helligkeit"] = request.form["form_helligkeit"]
        # Farben Amerikanisch
        for key in FARBEN_AMERIKANISCH:
            config["farben_amerikanisch"][key] = request.form[f"form_{key}"]
        # Farben GAFOR
        for key in FARBEN_GAFOR:
            config["farben_gafor"][key] = request.form[f"form_{key}"]
        # Wind
        config["wind"]["normal"] = request.form.get("form_normal", 15)
        config["wind"]["hoch"] = request.form.get("form_hoch", 25)
        config["wind"]["frequenz"] = request.form.get("form_frequenz", 1)
        # Zeiten
        config["zeiten"]["an"] = request.form.get("form_an", 8)
        config["zeiten"]["aus"] = request.form.get("form_aus", 22)
        dauerbetrieb = request.form.get("form_dauerbetrieb", False)  # wenn nicht checked dann wird es nicht submitted
        config["zeiten"]["dauerbetrieb"] = "true" if dauerbetrieb else "false"
        # Flugplätze
        config["flugplaetze"] = [i.strip() for i in request.form["form_flugplaetze"].split("\r")]

        # neue config parsen
        with open(f"{BASE_DIR}/config.yaml" if PI else "config.yaml", "w") as f:
            yaml.dump(config, f)

        if PI:

            # WLAN Einstellungen überarbeiten
            subprocess.call(["wpa_cli", "-i", "wlan0", "set_network", "0", "ssid", f'{config["wlan"]["ssid"]}'])
            subprocess.call(["wpa_cli", "-i", "wlan0", "set_network", "0", "psk", f'{config["wlan"]["passwort"]}'])

            # wieder mit dem normalen WLAN verbinden
            subprocess.call(["wpa_cli", "-i", "wlan0", "reconfigure"])
            logging.debug("wpa_cli ausgeführt")

            if config["zeiten"]["dauerbetrieb"] == "true":
                # Dauerbetrieb ist aktiv → cronjob anpassen, damit lightsoff.sh nicht ausgeführt wird
                with open(f"{BASE_DIR}/karte/crontab", "w+") as f:
                    cron_an = f"*/5 * * * *  {BASE_DIR}/karte/refresh.sh"
                    f.write(cron_an + "\n")
                subprocess.call(["sudo", "crontab", f"{BASE_DIR}/karte/crontab", "-"])
                logging.debug(f"cronjob angepasst: {cron_an}")
            else:
                # Dauerbetrieb ist aus → Zeiten in crontab schreiben
                with open(f"{BASE_DIR}/karte/crontab", "w+") as f:
                    cron_an = f"*/5 {config['zeiten']['an']}-{int(config['zeiten']['aus']) - 1} * * *  {BASE_DIR}/karte/refresh.sh"
                    cron_aus = f"*/5 {config['zeiten']['aus']} * * *     {BASE_DIR}/karte/lightsoff.sh"
                    f.write(cron_an + "\n")
                    f.write(cron_aus + "\n")
                subprocess.call(["sudo", "crontab", f"{BASE_DIR}/karte/crontab", "-"])
                logging.debug(f"cronjob angepasst: {cron_an} und {cron_aus}")

            # Update
            if request.form["form_update"] in ("main", "dev", "hotfix"):
                branch = "master" if request.form["form_update"] == "main" else request.form["form_update"]

                if branch:
                    logging.debug(f"git reset auf branch {branch}")

                    # repo auf den Stand des remote branches bringen
                    i = 0
                    repo = Repo(BASE_DIR)
                    while i < 6:
                        try:
                            repo.remotes.origin.fetch()
                            repo.git.reset("--hard")
                            repo.git.checkout(branch)
                            repo.git.reset("--hard")
                            repo.remotes.origin.pull()
                            i = 6
                        except:
                            logging.exception("git reset fehlgeschlagen")
                            sleep(10)
                            i += 1

                    # Permissions updaten, damit cron funktioniert und alle Skripte ausführbar sind
                    if PI:
                        subprocess.call(["sudo", "chmod", "+x", f"{BASE_DIR}/handle_permissions.sh"])
                        subprocess.call(["sudo", f"{BASE_DIR}/handle_permissions.sh"])

    return render_template("index.html", config=config, standard=standard, form=form, FARBEN_AMERIKANISCH=FARBEN_AMERIKANISCH, FARBEN_GAFOR=FARBEN_GAFOR)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=True)
