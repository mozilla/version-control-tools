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

import random
import os
from lockfiles import getlock, unlock
from subprocess import Popen, PIPE, STDOUT
from time import sleep
import urllib
import shlex

maxchildren = 3
random.seed()

# Spawn a child process for the given command
# return subprocess.Popen object
def spawn_child(cmd, verbose=False):
    proc = Popen(shlex.split(cmd), stdout=PIPE, stderr=STDOUT)
    if verbose:
        print "Spawned [%s] as pid %i" % (cmd, proc.pid)
    return proc

# Spawn subprocesses for each of the given commands, up to
# max_children.  Return a list of subprocess.Popen objects
def spawn_children(commands, max_children, verbose=False):
    procs = []
    while len(procs) < max_children and len(commands) > 0:
        p = spawn_child(commands[0], verbose)
        del commands[0]
        procs.append(p)
    if verbose:
        print "Spawned %i processes, %i pending" % ( len(procs), len(commands) )
    return procs

# check each child process, gather any output, 
def reap_children(children, verbose=False):
    if verbose:
        print "in reap_children, nchildren = %i" % len(children)
    for child in children:
        output = None
        rcode = child.poll()
        if(rcode != None):
            output = child.communicate()
            if verbose:
                print "%i exited with code %i" % (child.pid, rcode)
                if output:
                    print "Output: %s" % output[0]
            children.remove(child)
    return children

# Different repositories might get mirrored to different hosts.  For a
# given repository, return a list of hosts that should receive push
# notifications.  For the moment, this is hardcoded
def get_hosts_for_repo(repo):
    hosts = [ 'hg1.build.scl1.mozilla.com', 'hg1.build.scl1.mozilla.com' ]
    return hosts

def make_command(host, url_path, fh):
    return "sleep %i" % random.randint(5, 15)
    #return "/usr/bin/ssh %s mirror-pull %s" % (host, url_path)

def get_more_commands(directory, verbose=False):
    cmnds = []
    if verbose:
        print "Looking for files in %s" % directory
    dirh = os.listdir(directory)
    for f in dirh:
        f = "%s/%s" % (directory, f)
        lck = getlock(f, verbose)
        if lck:
            fh = file(f, 'r')
            os.unlink(f)
            unlock(f, lck, verbose)
            if verbose:
                print "Spawning a command..."
            for host in get_hosts_for_repo(urllib.unquote(f)):
                cmnds.append(make_command(host, urllib.unquote(f), fh))
            fh.close()
        else:
            print "Couldn't lock %s" % f
    return cmnds

def main():
    verbose  = True
    children = []
    commands = []
    dir = "/dev/shm/hg_pushes"
    while True:
        commands = commands + get_more_commands(dir, verbose)
        children = reap_children(children, verbose)
        children = children + spawn_children(commands, 
                                  maxchildren - len(children), 
                                  verbose)
        sleep(1)

if __name__ == "__main__":
    main()

