#!/usr/bin/env bash
# pip installieren
sudo apt install python3-pip -y
# pip requirements installieren
sudo pip3 install -r /home/pi/requirements.txt
sudo python3 -m pip install --force-reinstall adafruit-blinka
# berechtigungen vergeben
sudo chmod +x /home/pi/handle_permissions.sh
sudo /home/pi/handle_permissions.sh
# include karte/settings.py in rc.local
sudo sed -i '20isudo /usr/bin/python /home/pi/karte/settings.py > /home/pi/karte/settings-log.txt 2>&1 &' /etc/rc.local
# autoAP installieren
# TODO: ssh bricht ab, daher wird script nicht beendet
sudo /home/pi/install_autoap.sh