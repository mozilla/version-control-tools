#!/usr/bin/python

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
parser.add_option("-h", "--host", dest="tgt_host",
                  help="username@host to push to", metavar="USER@HOST")
(options, args) = parser.parse_args()

repo = options.repo
host = options.tgt_host

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
    print output
    break
  else:
    sleep(1)
