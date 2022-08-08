#!/usr/bin/env bash
# update
sudo apt update
sudo apt upgrade -y
# git und pip installieren
sudo apt install python3-pip -y
# pip requirements installieren
pip install -r /home/pi/requirements.txt
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
sudo /home/pi/install_autoap.sh