#!/bin/bash
# This script must be run as the postgres user

# create database
dropdb autoland
createdb autoland

# populate tables
psql autoland -f schema.sql
