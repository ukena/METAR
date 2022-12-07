pkill -F /home/metar/karte/offpid.pid
pkill -F /home/metar/karte/metarpid.pid
/usr/bin/python3 /home/metar/karte/pixelsoff.py & echo $! > /home/metar/karte/offpid.pid
