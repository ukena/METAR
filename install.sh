#!/usr/bin/env bash
# pip installieren
sudo apt install python3-pip -y
sudo apt install python3-git -y
# pip requirements installieren
sudo pip3 install -r /home/metar/requirements.txt
sudo python3 -m pip install --force-reinstall adafruit-blinka
# berechtigungen vergeben
sudo chmod +x /home/metar/handle_permissions.sh
sudo /home/metar/handle_permissions.sh
# karte/settings.py in rc.local für autostart eintragen
sudo sed -i '20isudo /usr/bin/python /home/metar/karte/settings.py > /home/metar/karte/settings-log.txt 2>&1 &' /etc/rc.local
# autoAP installieren
# TODO: ssh bricht ab, daher wird script nicht beendet
# Mgl. Lösung: ssh metar@host "nohup sudo /home/metar/install_autoap.sh > /dev/null 2>&1 &
# sudo /home/metar/install_autoap.sh
