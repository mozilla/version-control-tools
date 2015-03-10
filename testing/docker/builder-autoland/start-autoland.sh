#!/bin/bash

cd $AUTOLAND_HOME
. venv/bin/activate

cd autoland
python autoland_pulse.py --log-mach=/home/ubuntu/autoland-pulse.log --dsn="dbname=autoland user=postgres host=db" &
python autoland.py --log-mach=/home/ubuntu/autoland.log --dsn="dbname=autoland user=postgres host=db" &
apache2ctl -D FOREGROUND
