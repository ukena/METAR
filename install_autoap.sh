#!/usr/bin/env bash
# install autoap
sudo curl -L https://github.com/ukena/autoAP/raw/master/autoAP.sh -o /usr/local/bin/autoAP.sh
sudo curl -L https://github.com/ukena/autoAP/raw/master/install-autoAP -o /usr/local/bin/install-autoAP
sudo curl -L https://github.com/ukena/autoAP/raw/master/rpi-networkconfig -o /usr/local/bin/rpi-networkconfig
sudo chmod 755 /usr/local/bin/autoAP.sh /usr/local/bin/install-autoAP /usr/local/bin/rpi-networkconfig
printf "METAR\nMETARKARTE\n\ny\n" | sudo /usr/local/bin/install-autoAP
printf "\n" | sudo /usr/local/bin/rpi-networkconfig
# include karte/settings.py in rc.local
sudo sed -i '18i  sudo /usr/bin/python3 /home/pi/karte/settings.py' /etc/rc.local
# reboot
sudo reboot