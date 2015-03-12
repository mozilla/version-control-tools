#!/bin/bash
ps -e|grep python|awk '{split($1,x," "); print(x[1])}'|xargs kill
hg pull
hg update
rm -rf venv
virtualenv venv
. venv/bin/activate
pip install -r requirements.txt
cd autoland
nohup ./autoland_pulse.py --log-mach=/home/ubuntu/autoland-pulse.log &
nohup ./autoland.py --log-mach=/home/ubuntu/autoland.log &
