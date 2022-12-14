#!/usr/bin/env bash
# # # # # # # # # # # # # # # # # Vorher # # # # # # # # # # # # # # # # #
# sudo apt update
# sudo apt upgrade -y
# sudo apt install -y git
# sudo chmod +x /home/metar/install.sh
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# ssh metar@metarmap "nohup sudo /home/metar/install.sh > /dev/null 2>&1 &"
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# pip, git und lxml installieren
sudo apt install python3-pip -y
sudo apt install python3-git -y
sudo apt install libxslt-dev -y
# pip requirements installieren
sudo pip3 install -r /home/metar/requirements.txt
sudo python3 -m pip install --force-reinstall adafruit-blinka
# berechtigungen vergeben
sudo chmod +x /home/metar/handle_permissions.sh
sudo /home/metar/handle_permissions.sh
# karte/settings.py in rc.local für autostart eintragen
sudo sed -i '20isudo /usr/bin/python /home/metar/karte/settings.py > /home/metar/karte/settings-log.txt 2>&1 &' /etc/rc.local
# autoAP installieren
sudo /home/metar/install_autoap.sh
