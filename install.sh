#!/usr/bin/env bash
# pip installieren
sudo apt install python3-pip -y
# pip requirements installieren
suod pip3 install -r /home/pi/requirements.txt
sudo python3 -m pip install --force-reinstall adafruit-blinka
# berechtigungen vergeben
sudo chmod +x /home/pi/install_autoap.sh
sudo chmod +x /home/pi/karte/refresh.sh
sudo chmod +x /home/pi/karte/lightsoff.sh
sudo chmod +r /home/pi/karte/metar.py
sudo chmod +r /home/pi/karte/pixelsoff.py
sudo chmod +r /home/pi/config.yaml
# include karte/settings.py in rc.local
sudo sed -i '20isudo /usr/bin/python /home/pi/karte/settings.py > /home/pi/karte/settings-log.txt 2>&1 &' /etc/rc.local
# autoAP installieren
# TODO: ssh bricht ab, daher wird script nicht beendet
sudo /home/pi/install_autoap.sh