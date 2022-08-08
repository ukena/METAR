#!/usr/bin/env bash
# berechtigungen vergeben
sudo chmod +x /home/pi/install_autoap.sh
sudo chmod +x /home/pi/karte/refresh.sh
sudo chmod +x /home/pi/karte/lightsoff.sh
sudo chmod +r /home/pi/karte/metar.py
sudo chmod +r /home/pi/karte/pixelsoff.py
sudo chmod +r /home/pi/config.yaml
# include karte/settings.py in rc.local
sudo sed -i '18i  sudo /usr/bin/python /home/pi/karte/settings.py > /home/pi/web/log.txt 2>&1 &' /etc/rc.local
# autoAP installieren
sudo /home/pi/install_autoap.sh