#!/bin/bash
# This script must be run as the postgres user
# e.g. sudo -u postgres ./createdb.sh

if [ -z $HOST ]
then
    HOST=/var/run/postgresql
fi

if [ -z $PORT ]
then
    PORT=5432
fi

dropdb -h $HOST -p $PORT -U postgres autoland
dropdb -h $HOST -p $PORT -U postgres testautoland

dropuser -h $HOST -p $PORT -U postgres autoland
createuser -h $HOST -p $PORT -U postgres autoland -S -D -R

createdb -h $HOST -p $PORT -U postgres autoland
psql -h $HOST -p $PORT -U postgres autoland -f schema.sql

createdb -h $HOST -p $PORT -U postgres testautoland
psql -h $HOST -p $PORT -U postgres testautoland -f schema.sql
