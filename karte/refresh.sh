pkill -F /home/pi/karte/offpid.pid
pkill -F /home/pi/karte/metarpid.pid
/usr/bin/python3 /home/pi/karte/metar.py & echo $! > /home/pi/karte/metarpid.pid
