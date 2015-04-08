#!/bin/bash
# This script must be run as the postgres user
# e.g. sudo -u postgres ./updatedb.sh add-foo.sql

if [ -z $HOST ]
then
    HOST=/var/run/postgresql
fi

if [ -z $PORT ]
then
    PORT=5432
fi

psql -h $HOST -p $PORT -U postgres autoland -f $1 
