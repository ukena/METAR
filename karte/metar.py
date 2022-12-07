#!/usr/bin/env python3
import yaml
import urllib.request
import xml.etree.ElementTree as ET
import board
import neopixel
import time
import datetime
import logging
import requests

logging.basicConfig(filename='/home/metar/karte/debug.log', encoding='utf-8', level=logging.DEBUG, force=True)

def hex_to_grb(hex_color):
    hex_color = hex_color.replace("#", "")
    grb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return grb

config = yaml.safe_load(open("/home/metar/config.yaml"))

# version kann "gafor" oder "amerikanisch" sein
version = config["version"]

LED_COUNT = 100
LED_PIN = board.D18
LED_BRIGHTNESS = float(config["helligkeit"])
LED_ORDER = neopixel.GRB
COLOR_CLEAR = (0, 0, 0)

# Farben Amerikanisch
COLOR_VFR = hex_to_grb(config["farben_amerikanisch"]["vfr"])
COLOR_VFR_FADE = hex_to_grb(config["farben_amerikanisch"]["vfr_bei_wind"])
COLOR_MVFR = hex_to_grb(config["farben_amerikanisch"]["mvfr"])
COLOR_MVFR_FADE = hex_to_grb(config["farben_amerikanisch"]["mvfr_bei_wind"])
COLOR_IFR = hex_to_grb(config["farben_amerikanisch"]["ifr"])
COLOR_IFR_FADE = hex_to_grb(config["farben_amerikanisch"]["ifr_bei_wind"])
COLOR_LIFR = hex_to_grb(config["farben_amerikanisch"]["lifr"])
COLOR_LIFR_FADE = hex_to_grb(config["farben_amerikanisch"]["lifr_bei_wind"])
COLOR_LIGHTNING = hex_to_grb(config["farben_amerikanisch"]["blitze-amerikanisch"])
COLOR_HIGH_WINDS = hex_to_grb(config["farben_amerikanisch"]["hoher_wind"])

# Farben GAFOR
COLOR_GAFOR_C = hex_to_grb(config["farben_gafor"]["charlie"])
COLOR_GAFOR_C_WIND = hex_to_grb(config["farben_gafor"]["charlie_bei_wind"])
COLOR_GAFOR_O = hex_to_grb(config["farben_gafor"]["oscar"])
COLOR_GAFOR_O_WIND = hex_to_grb(config["farben_gafor"]["oscar_bei_wind"])
COLOR_GAFOR_D = hex_to_grb(config["farben_gafor"]["delta"])
COLOR_GAFOR_D_WIND = hex_to_grb(config["farben_gafor"]["delta_bei_wind"])
COLOR_GAFOR_M = hex_to_grb(config["farben_gafor"]["mike"])
COLOR_GAFOR_M_WIND = hex_to_grb(config["farben_gafor"]["mike_bei_wind"])
COLOR_GAFOR_X = hex_to_grb(config["farben_gafor"]["xray"])
COLOR_GAFOR_X_WIND = hex_to_grb(config["farben_gafor"]["xray_bei_wind"])
COLOR_GAFOR_BLITZE = hex_to_grb(config["farben_gafor"]["blitze-gafor"])

# Windgeschwindigkeiten und Frequenz
WIND_BLINK_THRESHOLD = int(config["wind"]["normal"])
HIGH_WINDS_THRESHOLD = int(config["wind"]["hoch"])
BLINK_SPEED = float(config["wind"]["frequenz"])
BLINK_TOTALTIME_SECONDS = 300

# LEDs instanziieren
pixels = neopixel.NeoPixel(LED_PIN, LED_COUNT, brightness=LED_BRIGHTNESS, pixel_order=LED_ORDER, auto_write=False)

# ICAO Codes der Flugplätze für die Reihenfolge als Liste
flugplaetze = [x.strip() for x in config["flugplaetze"]]

# METAR als XML abfragen
url = "https://www.aviationweather.gov/adds/dataserver_current/httpparam?dataSource=metars&requestType=retrieve&format=xml&hoursBeforeNow=5&mostRecentForEachStation=true&stationString=" + ",".join(
    [item for item in flugplaetze if item != "NULL"])
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36 Edg/86.0.622.69'}
content = requests.get(url, headers=headers).text

# XML parsen
root = ET.fromstring(content)

# dictionary für jede Beobachtung
beobachtung = {}

# über jedes METAR iterieren
for metar in root.iter('METAR'):
    # ICAO Code des Flugplatzes
    stations_id = metar.find('station_id').text

    # wenn keine flight_category vorhanden ist, dann überspringe das METAR
    if metar.find('flight_category') is None:
        logging.warning("Keine flight_category für " + stations_id)
        continue

    # Variablen für die Beobachtung
    flightCategory = metar.find('flight_category').text
    wind_richtung = ""
    wind_geschwindigkeit_kt = 0
    hoher_wind_knoten = 0
    hoher_wind = False
    blitze = False
    temp_c = 0
    taupunkt_c = 0
    sichtweite_km = 0
    luftdruck_inhg = 0.0
    wettererscheinung = ""

    # Liste für alle Wolkenuntergrenzen und Bedeckungsgrad für das jeweilige METAR
    alle_wolken_bedingungen = []

    # wenn es böig ist, dann setze hoher_wind auf True
    if metar.find('wind_gust_kt') is not None:
        hoher_wind_knoten = int(metar.find('wind_gust_kt').text)
        hoher_wind = (True if (hoher_wind_knoten > WIND_BLINK_THRESHOLD) else False)

    # Windgeschwindigkeit in knoten
    if metar.find('wind_speed_kt') is not None:
        wind_geschwindigkeit_kt = int(metar.find('wind_speed_kt').text)

    # Windrichtung
    if metar.find('wind_dir_degrees') is not None:
        wind_richtung = metar.find('wind_dir_degrees').text

    # Temperatur in °C
    if metar.find('temp_c') is not None:
        temp_c = int(round(float(metar.find('temp_c').text)))

    # Taupunkt in °C
    if metar.find('dewpoint_c') is not None:
        taupunkt_c = int(round(float(metar.find('dewpoint_c').text)))

    # Sichtweite in Statute Miles → Umrechnung in km
    if metar.find('visibility_statute_mi') is not None:
        sichtweite_sm = float(metar.find('visibility_statute_mi').text)
        sichtweite_km = round(sichtweite_sm / 0.62137119223733, 1)

    # Luftdruck in inHg
    if metar.find('altim_in_hg') is not None:
        luftdruck_inhg = float(round(float(metar.find('altim_in_hg').text), 2))

    # weiter Wettererscheinungen (z.B. -RA)
    if metar.find('wx_string') is not None:
        wettererscheinung = metar.find('wx_string').text

    # Zeitpunkt der Beobachtung
    if metar.find('observation_time') is not None:
        zeitpunkt = datetime.datetime.fromisoformat(metar.find('observation_time').text.replace("Z", "+00:00"))

    # alle Wolkendecken mit Wolkenuntergrenze und Bedeckungsgrad erfassen
    for wolken_iter in metar.iter("sky_condition"):
        wolken_bedingung = {"cover": wolken_iter.get("sky_cover"), "cloudBaseFt": int(wolken_iter.get("cloud_base_ft_agl", default=0))}
        alle_wolken_bedingungen.append(wolken_bedingung)

    # METAR nach Wettererscheinungen die auf Blitze hindeuten filtern
    if metar.find('raw_text') is not None:
        metar_text = metar.find('raw_text').text
        blitze = False if ((metar_text.find('LTG', 4) == -1 and metar_text.find('TS', 4) == -1) or metar_text.find('TSNO', 4) != -1) else True

    # dictionary mit den Beobachtungen füllen
    beobachtung[stations_id] = {"flightCategory": flightCategory, "windDir": wind_richtung, "windSpeed": wind_geschwindigkeit_kt,
                                "windGustSpeed": hoher_wind_knoten, "windGust": hoher_wind, "vis": sichtweite_km, "obs": wettererscheinung,
                                "tempC": temp_c, "dewpointC": taupunkt_c, "altimHg": luftdruck_inhg, "lightning": blitze,
                                "skyConditions": alle_wolken_bedingungen, "obsTime": zeitpunkt}

# Blinkfrequenz der LEDs berechnen
looplimit = int(round(BLINK_TOTALTIME_SECONDS / BLINK_SPEED))

# jede zweite Iteration wird bei blinkenden Lichtern die Farbe gewechselt
windCycle = False

# bis die Daten neu abgefragt werden (default alle 5 min)
while looplimit > 0:
    i = 0
    for icao in flugplaetze:
        if icao == "NULL":
            i += 1
            continue

        color = COLOR_CLEAR
        conditions = beobachtung.get(icao, None)
        windy = False
        highWinds = False
        lightningConditions = False

        if conditions != None:
            windy = True if (windCycle == True and (conditions["windSpeed"] >= WIND_BLINK_THRESHOLD or conditions["windGust"] == True)) else False
            highWinds = True if (windy and version != "gafor" and HIGH_WINDS_THRESHOLD != -1 and (
                        conditions["windSpeed"] >= HIGH_WINDS_THRESHOLD or conditions[
                    "windGustSpeed"] >= HIGH_WINDS_THRESHOLD)) else False
            lightningConditions = True if (windCycle == False and conditions["lightning"] == True) else False

            # gafor version
            if version == "gafor":
                if conditions["vis"] < 1.5 or any(sc["cloudBaseFt"] < 500 and sc["cover"] in ("BKN", "OVC") for sc in conditions["skyConditions"]):
                    color = COLOR_GAFOR_X if not (windy or lightningConditions) else COLOR_GAFOR_BLITZE if lightningConditions else COLOR_GAFOR_X_WIND if windy else COLOR_CLEAR
                    logging.debug(f"setting {icao} to X {conditions['vis']} {conditions['skyConditions']}; wind: {conditions['windSpeed']}")
                elif (5 > conditions["vis"] >= 1.5) or any(1000 > sc["cloudBaseFt"] >= 500 and sc["cover"] in ("BKN", "OVC") for sc in conditions["skyConditions"]):
                    color = COLOR_GAFOR_M if not (windy or lightningConditions) else COLOR_GAFOR_BLITZE if lightningConditions else COLOR_GAFOR_M_WIND if windy else COLOR_CLEAR
                    logging.debug(f"setting {icao} to M {conditions['vis']} {conditions['skyConditions']}; wind: {conditions['windSpeed']}")
                elif (8 > conditions["vis"] >= 5) or any(2000 > sc["cloudBaseFt"] >= 1000 and sc["cover"] in ("BKN", "OVC") for sc in conditions["skyConditions"]):
                    color = COLOR_GAFOR_D if not (windy or lightningConditions) else COLOR_GAFOR_BLITZE if lightningConditions else COLOR_GAFOR_D_WIND if windy else COLOR_CLEAR
                    logging.debug(f"setting {icao} to D {conditions['vis']} {conditions['skyConditions']}; wind: {conditions['windSpeed']}")
                elif (10 > conditions["vis"] >= 8) or any(5000 > sc["cloudBaseFt"] >= 2000 and sc["cover"] in ("BKN", "OVC") for sc in conditions["skyConditions"]):
                    color = COLOR_GAFOR_O if not (windy or lightningConditions) else COLOR_GAFOR_BLITZE if lightningConditions else COLOR_GAFOR_O_WIND if windy else COLOR_CLEAR
                    logging.debug(f"setting {icao} to O {conditions['vis']} {conditions['skyConditions']}; wind: {conditions['windSpeed']}")
                elif (conditions["vis"] >= 10) or any(sc["cloudBaseFt"] >= 5000 and sc["cover"] in ("BKN", "OVC") for sc in conditions["skyConditions"]):
                    color = COLOR_GAFOR_C if not (windy or lightningConditions) else COLOR_GAFOR_BLITZE if lightningConditions else COLOR_GAFOR_C_WIND if windy else COLOR_CLEAR
                    logging.debug(f"setting {icao} to C {conditions['vis']} {conditions['skyConditions']}; wind: {conditions['windSpeed']}")
                else:
                    color = COLOR_CLEAR

            # amerikanische version
            elif version == "amerikanisch":
                if conditions["flightCategory"] == "VFR":
                    color = COLOR_VFR if not (windy or lightningConditions) else COLOR_LIGHTNING if lightningConditions else COLOR_HIGH_WINDS if highWinds else COLOR_VFR_FADE if windy else COLOR_CLEAR
                elif conditions["flightCategory"] == "MVFR":
                    color = COLOR_MVFR if not (windy or lightningConditions) else COLOR_LIGHTNING if lightningConditions else COLOR_HIGH_WINDS if highWinds else COLOR_MVFR_FADE if windy else COLOR_CLEAR
                elif conditions["flightCategory"] == "IFR":
                    color = COLOR_IFR if not (windy or lightningConditions) else COLOR_LIGHTNING if lightningConditions else COLOR_HIGH_WINDS if highWinds else COLOR_IFR_FADE if windy else COLOR_CLEAR
                elif conditions["flightCategory"] == "LIFR":
                    color = COLOR_LIFR if not (windy or lightningConditions) else COLOR_LIGHTNING if lightningConditions else COLOR_HIGH_WINDS if highWinds else COLOR_LIFR_FADE if windy else COLOR_CLEAR
                else:
                    color = COLOR_CLEAR

        pixels[i] = color
        i += 1

    # legende gafor
    if version == "gafor":
        pixels[i + 6] = COLOR_GAFOR_C
        pixels[i + 5] = COLOR_GAFOR_O
        pixels[i + 4] = COLOR_GAFOR_D
        pixels[i + 3] = COLOR_GAFOR_M
        pixels[i + 2] = COLOR_GAFOR_X
        pixels[i + 1] = COLOR_GAFOR_BLITZE if windCycle else COLOR_GAFOR_C
        pixels[i] = COLOR_GAFOR_C if not windCycle else COLOR_GAFOR_C_WIND
    # legende amerikanisch
    elif version == "amerikanisch":
        pixels[i + 6] = COLOR_VFR
        pixels[i + 5] = COLOR_MVFR
        pixels[i + 4] = COLOR_IFR
        pixels[i + 3] = COLOR_LIFR
        pixels[i + 2] = COLOR_LIGHTNING if windCycle else COLOR_VFR
        pixels[i + 1] = COLOR_VFR if not windCycle else COLOR_VFR_FADE
        pixels[i] = COLOR_VFR if not windCycle else COLOR_HIGH_WINDS

    pixels.show()

    time.sleep(BLINK_SPEED)
    windCycle = False if windCycle else True
    looplimit -= 1
