#!/bin/bash

cd $AUTOLAND_HOME
. venv/bin/activate

cd autoland

PID=$(ps x | grep python | grep -v grep | awk '{ print $1 }')
[ -n "$PID" ] && kill $PID
(python autoland.py --dsn="dbname=autoland user=postgres host=autolanddb" >& /home/autoland/autoland.log) &

if [ -n "$(ps x | grep apache2 | grep -v grep | grep -v apache2ctl)" ]; then
  apache2ctl restart
else
  apache2ctl -D FOREGROUND
fi
