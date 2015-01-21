#!/bin/bash

cd $AUTOLAND_HOME 
. venv/bin/activate

cd sql
HOST=db ./createdb.sh

cd ../autoland
python autoland_pulse.py --log-mach=- --dsn="dbname=autoland user=postgres host=db" &
python autoland.py --log-mach=- --dsn="dbname=autoland user=postgres host=db" &
tail -f /var/log/apache2/error.log &
apache2ctl -D FOREGROUND
