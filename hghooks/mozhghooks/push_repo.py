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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.

import sys
sys.path.append('/repo/hg/libraries/mozhghoooks')

from optparse import OptionParser
from mirror_daemon import *
from time import sleep

configfile = "/etc/mercurial/repo-mirrors.yaml"
cfg = read_config(configfile)

parser = OptionParser()
parser.add_option("-r", "--repo", dest="repo", 
                  help="Repository path, relative to http://hg.m.o", 
                  metavar="REPO")
parser.add_option("-H", "--host", dest="tgt_host",
                  help="username@host to push to", metavar="USER@HOST")
(options, args) = parser.parse_args()

repo = options.repo
host = options.tgt_host

if not repo or not host:
    parser.print_help()
    sys.exit(1)

# Read some global values from the config file, filling in
# some sane-ish defaults for missing values.
verbose = get_config_key(cfg, ['daemon', 'verbose'])
maxchildren = 1

job = MirrorJob(host, repo, cfg, None, True)
job.spawn_child()

while True:
  rcode = job.child.poll()
  if rcode != None:
    output = job.child.communicate()
    print "Job finished with code %i. Output follows:" % rcode
    print output[0]
    break
  else:
    sleep(1)
