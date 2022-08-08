/usr/bin/sudo pkill -F /home/pi/karte/offpid.pid
/usr/bin/sudo pkill -F /home/pi/karte/metarpid.pid
/usr/bin/sudo /usr/bin/python3 /home/pi/karte/metar.py & echo $! > /home/pi/karte/metarpid.pid
