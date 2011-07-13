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
import yaml

maxchildren = 3
configfile = "/etc/mercurial/repo-mirrors.yaml"
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
def get_hosts_for_repo(repo, config):
    hosts = []
    if(config.has_key(repo)):
        hosts = config[repo]['mirrors']
    return hosts

def make_command(host, url_path, config, fh):
    if config.has_key('daemon') and config['daemon'].has_key('ssh-id'):
        id_str = "-i%s" % config['daemon']['ssh-id']
    else:
        id_str = ""
    return "/usr/bin/ssh -n %s %s hg pull %s" % (id_str, host, url_path)

def get_more_commands(directory, config, verbose=False):
    cmnds = []
    if verbose:
        print "Looking for files in %s" % directory
    dirh = os.listdir(directory)
    for f in dirh:
        fullpath = "%s/%s" % (directory, f)
        lck = getlock(fullpath, verbose)
        if lck:
            fh = file(fullpath, 'r')
            os.unlink(fullpath)
            unlock(fullpath, lck, verbose)
            for host in get_hosts_for_repo(urllib.unquote(f), config):
                cmnds.append(make_command(host, 
                                          urllib.unquote(f), 
                                          config,
                                          fh))
                if verbose:
                    print "Appended a command to the queue. ",
                    print "qlen: %i" % len(cmnds)
            fh.close()
        else:
            print "Couldn't lock %s" % fullpath
    return cmnds

# Read the config file. Returns a dictionary object, which may be empty
def read_config():
    try:
        f = file(configfile)
    except IOError, e:
        print "WARNING: mirror config %s: %s" % (configfile, e)
        return {}
    y = yaml.load(f)
    f.close()
    if y == None:
        y = {}
    return y

def main():
    verbose  = True
    children = []
    commands = []
    dir = "/dev/shm/hg_pushes"
    cfg = read_config()
    while True:
        commands = commands + get_more_commands(dir, cfg, verbose)
        children = reap_children(children, verbose)
        children = children + spawn_children(commands, 
                                  maxchildren - len(children), 
                                  verbose)
        sleep(1)

if __name__ == "__main__":
    main()

