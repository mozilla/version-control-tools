#!/usr/bin/python

from os import open, close, read, unlink, O_CREAT, O_EXCL
from time import sleep

def getlock(fname, verbose=False):
    maxtries=3
    lockf="%s.lck" % fname
    fd = False
    for i in range(0,maxtries):
        try:
            fd = open(lockf, O_CREAT|O_EXCL)
            if verbose:
                print "Locked %s" % fname
            return fd
        except OSError:
            tries=maxtries-i
            if verbose:
                print "Could not lock %s" % fname
                print "  Will try %i more times" % tries
            sleep(1)
    return fd

def unlock(fname, fd, verbose=False):
    if verbose:
        print "Unlocking %s" % fname
    lockf = "%s.lck" % fname
    close(fd)
    unlink(lockf)

