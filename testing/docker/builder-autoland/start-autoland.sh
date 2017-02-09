#!/bin/bash

cd $AUTOLAND_HOME
. venv/bin/activate

cd autoland
(python autoland.py --dsn="dbname=autoland user=postgres host=autolanddb" >& /home/autoland/autoland.log) &
apache2ctl -D FOREGROUND
