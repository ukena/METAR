pkill -F /home/pi/karte/offpid.pid
pkill -F /home/pi/karte/metarpid.pid
/usr/bin/python3 /home/pi/karte/pixelsoff.py & echo $! > /home/pi/karte/offpid.pid
