#!/bin/bash

cd $AUTOLAND_HOME
. venv/bin/activate

cd autoland
python autoland.py --log-path=/home/autoland/autoland.log --dsn="dbname=autoland user=postgres host=autolanddb" &
apache2ctl -D FOREGROUND
