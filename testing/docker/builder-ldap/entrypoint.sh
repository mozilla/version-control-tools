#!/bin/bash

# This is needed to keep slapd memory usage in check.
ulimit -n 1024

exec "$@"
