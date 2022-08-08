#!/usr/bin/env bash
# install autoap
sudo curl -L https://github.com/ukena/autoAP/raw/master/autoAP.sh -o /usr/local/bin/autoAP.sh
sudo curl -L https://github.com/ukena/autoAP/raw/master/install-autoAP -o /usr/local/bin/install-autoAP
sudo curl -L https://github.com/ukena/autoAP/raw/master/rpi-networkconfig -o /usr/local/bin/rpi-networkconfig
sudo chmod 755 /usr/local/bin/autoAP.sh /usr/local/bin/install-autoAP /usr/local/bin/rpi-networkconfig
printf "METAR\nMETARKARTE\n\ny\n" | sudo /usr/local/bin/install-autoAP
printf "\n" | sudo /usr/local/bin/rpi-networkconfig
# handle permissions
sudo chmod +x /home/pi/karte/refresh.sh
sudo chmod +x /home/pi/karte/lightsoff.sh
sudo chmod +r /home/pi/karte/metar.py
sudo chmod +r /home/pi/karte/pixelsoff.py
sudo chmod +r /home/pi/config.yaml
# reboot
sudo reboot