#!/usr/bin/env bash
# install autoap
sudo curl -L https://github.com/ukena/autoAP/raw/master/autoAP.sh -o /usr/local/bin/autoAP.sh
sudo curl -L https://github.com/ukena/autoAP/raw/master/install-autoAP -o /usr/local/bin/install-autoAP
sudo curl -L https://github.com/ukena/autoAP/raw/master/rpi-networkconfig -o /usr/local/bin/rpi-networkconfig
sudo chmod 755 /usr/local/bin/autoAP.sh /usr/local/bin/install-autoAP /usr/local/bin/rpi-networkconfig
printf "METAR\nMETARMAP\n\ny\n" | sudo /usr/local/bin/install-autoAP
printf "\n" | sudo /usr/local/bin/rpi-networkconfig
# reboot
sudo reboot