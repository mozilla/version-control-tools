#!/usr/bin/python
# Copyright (C) 2011 Mozilla Foundation
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

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

