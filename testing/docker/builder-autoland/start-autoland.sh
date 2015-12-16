#!/bin/bash

cd $AUTOLAND_HOME
. venv/bin/activate

cd autoland
python autoland.py --log-path=/home/ubuntu/autoland.log --dsn="dbname=autoland user=postgres host=db" &
apache2ctl -D FOREGROUND
