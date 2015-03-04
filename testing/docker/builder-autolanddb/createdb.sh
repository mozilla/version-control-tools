#!/bin/bash
gosu postgres postgres --single <<- EOSQL
    CREATE USER autoland;
    CREATE DATABASE autoland;
EOSQL

gosu postgres postgres --single autoland < /docker-entrypoint-initdb.d/schema.sql
