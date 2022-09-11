#!/usr/bin/env python3
import yaml
import urllib.request
import xml.etree.ElementTree as ET
import board
import neopixel
import time
import datetime

def hex_to_grb(hex_color):
    hex_color = hex_color.replace("#", "")
    grb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return grb

config = yaml.safe_load(open("/home/pi/config.yaml"))

# version kann "gafor" oder "amerikanisch" sein
version = config["version"]

LED_COUNT = 100
LED_PIN = board.D18
LED_BRIGHTNESS = float(config["farben_amerikanisch"]["helligkeit"]) if version == "amerikanisch" else float(config["farben_gafor"]["helligkeit"])
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
COLOR_LIGHTNING = hex_to_grb(config["farben_amerikanisch"]["blitze"])
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
COLOR_GAFOR_BLITZE = hex_to_grb(config["farben_gafor"]["blitze"])

WIND_BLINK_THRESHOLD = int(config["wind"]["normal"])
HIGH_WINDS_THRESHOLD = int(config["wind"]["hoch"])
BLINK_SPEED = float(config["wind"]["frequenz"])

BLINK_TOTALTIME_SECONDS = 300

SHOW_LEGEND = True
OFFSET_LEGEND_BY = 0

# Initialize the LED strip
pixels = neopixel.NeoPixel(LED_PIN, LED_COUNT, brightness=LED_BRIGHTNESS, pixel_order=LED_ORDER, auto_write=False)

# Read the airports file to retrieve list of airports and use as order for LEDs
airports = [x.strip() for x in config["flugplaetze"]]

url = "https://www.aviationweather.gov/adds/dataserver_current/httpparam?dataSource=metars&requestType=retrieve&format=xml&hoursBeforeNow=5&mostRecentForEachStation=true&stationString=" + ",".join(
    [item for item in airports if item != "NULL"])

req = urllib.request.Request(url, headers={
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36 Edg/86.0.622.69'})
content = urllib.request.urlopen(req).read()

root = ET.fromstring(content)
conditionDict = {"NULL": {"flightCategory": "", "windDir": "", "windSpeed": 0, "windGustSpeed": 0, "windGust": False,
                          "lightning": False, "tempC": 0, "dewpointC": 0, "vis": 0, "altimHg": 0, "obs": "",
                          "skyConditions": {}, "obsTime": datetime.datetime.now()}}
conditionDict.pop("NULL")
stationList = []

for metar in root.iter('METAR'):
    stationId = metar.find('station_id').text
    if metar.find('flight_category') is None:
        print("Missing flight condition, skipping.")
        continue
    flightCategory = metar.find('flight_category').text
    windDir = ""
    windSpeed = 0
    windGustSpeed = 0
    windGust = False
    lightning = False
    tempC = 0
    dewpointC = 0
    vis = 0
    altimHg = 0.0
    obs = ""
    skyConditions = []
    if metar.find('wind_gust_kt') is not None:
        windGustSpeed = int(metar.find('wind_gust_kt').text)
        windGust = (True if (windGustSpeed > WIND_BLINK_THRESHOLD) else False)
    if metar.find('wind_speed_kt') is not None:
        windSpeed = int(metar.find('wind_speed_kt').text)
    if metar.find('wind_dir_degrees') is not None:
        windDir = metar.find('wind_dir_degrees').text
    if metar.find('temp_c') is not None:
        tempC = int(round(float(metar.find('temp_c').text)))
    if metar.find('dewpoint_c') is not None:
        dewpointC = int(round(float(metar.find('dewpoint_c').text)))
    if metar.find('visibility_statute_mi') is not None:
        vis = float(metar.find('visibility_statute_mi').text)
        vis = round(vis / 0.62137119223733, 1)
    if metar.find('altim_in_hg') is not None:
        altimHg = float(round(float(metar.find('altim_in_hg').text), 2))
    if metar.find('wx_string') is not None:
        obs = metar.find('wx_string').text
    if metar.find('observation_time') is not None:
        obsTime = datetime.datetime.fromisoformat(metar.find('observation_time').text.replace("Z", "+00:00"))
    for skyIter in metar.iter("sky_condition"):
        skyCond = {"cover": skyIter.get("sky_cover"), "cloudBaseFt": int(skyIter.get("cloud_base_ft_agl", default=0))}
        skyConditions.append(skyCond)
    if metar.find('raw_text') is not None:
        rawText = metar.find('raw_text').text
        lightning = False if ((rawText.find('LTG', 4) == -1 and rawText.find('TS', 4) == -1) or rawText.find('TSNO',
                                                                                                             4) != -1) else True
    conditionDict[stationId] = {"flightCategory": flightCategory, "windDir": windDir, "windSpeed": windSpeed,
                                "windGustSpeed": windGustSpeed, "windGust": windGust, "vis": vis, "obs": obs,
                                "tempC": tempC, "dewpointC": dewpointC, "altimHg": altimHg, "lightning": lightning,
                                "skyConditions": skyConditions, "obsTime": obsTime}
    stationList.append(stationId)

looplimit = int(round(BLINK_TOTALTIME_SECONDS / BLINK_SPEED))

windCycle = False

while looplimit > 0:
    i = 0
    for airportcode in airports:
        if airportcode == "NULL":
            i += 1
            continue

        color = COLOR_CLEAR
        conditions = conditionDict.get(airportcode, None)
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
                    color = COLOR_GAFOR_X
                elif (5 > conditions["vis"] >= 1.5) or any(1000 > sc["cloudBaseFt"] >= 500 and sc["cover"] in ("BKN", "OVC") for sc in conditions["skyConditions"]):
                    color = COLOR_GAFOR_M
                elif (8 > conditions["vis"] >= 5) or any(2000 > sc["cloudBaseFt"] >= 1000 and sc["cover"] in ("BKN", "OVC") for sc in conditions["skyConditions"]):
                    color = COLOR_GAFOR_D
                elif (10 > conditions["vis"] >= 8) or any(5000 > sc["cloudBaseFt"] >= 2000 and sc["cover"] in ("BKN", "OVC") for sc in conditions["skyConditions"]):
                    color = COLOR_GAFOR_O
                elif (conditions["vis"] >= 10) or any(sc["cloudBaseFt"] >= 5000 and sc["cover"] in ("BKN", "OVC") for sc in conditions["skyConditions"]):
                    color = COLOR_GAFOR_C

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

    if SHOW_LEGEND:
        if version == "gafor":
            pixels[i + OFFSET_LEGEND_BY] = COLOR_GAFOR_C
            pixels[i + OFFSET_LEGEND_BY + 1] = COLOR_GAFOR_O
            pixels[i + OFFSET_LEGEND_BY + 2] = COLOR_GAFOR_D
            pixels[i + OFFSET_LEGEND_BY + 3] = COLOR_GAFOR_M
            pixels[i + OFFSET_LEGEND_BY + 4] = COLOR_GAFOR_X
            pixels[i + OFFSET_LEGEND_BY + 4] = COLOR_GAFOR_BLITZE if windCycle else COLOR_GAFOR_C
            pixels[i + OFFSET_LEGEND_BY + 5] = COLOR_GAFOR_C if not windCycle else COLOR_GAFOR_C_WIND

        elif version == "amerikanisch":
            pixels[i + OFFSET_LEGEND_BY] = COLOR_VFR
            pixels[i + OFFSET_LEGEND_BY + 1] = COLOR_MVFR
            pixels[i + OFFSET_LEGEND_BY + 2] = COLOR_IFR
            pixels[i + OFFSET_LEGEND_BY + 3] = COLOR_LIFR
            pixels[i + OFFSET_LEGEND_BY + 4] = COLOR_LIGHTNING if windCycle else COLOR_VFR
            pixels[i + OFFSET_LEGEND_BY + 5] = COLOR_VFR if not windCycle else COLOR_VFR_FADE
            if HIGH_WINDS_THRESHOLD != -1:
                pixels[i + OFFSET_LEGEND_BY + 6] = COLOR_VFR if not windCycle else COLOR_HIGH_WINDS

    pixels.show()

    time.sleep(BLINK_SPEED)
    windCycle = False if windCycle else True
    looplimit -= 1
