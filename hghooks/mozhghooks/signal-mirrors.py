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

import os
import time
from mercurial import hg, ui, commands, node
import re
import urllib
from lockfiles import getlock, unlock

repo_toplevel="/repo/hg/mozilla"
workdir="/dev/shm/hg_pushes"

def hook(ui, repo, **kwargs):
    if not os.path.isdir(workdir):
        os.mkdir(workdir)
    repo_name = os.path.basename(repo.root)
    url_path = re.sub('^%s' % repo_toplevel, '', repo.root)
    # Escape '/' characters in url path, so we can store this
    # info in a filename:
    escaped_path = urllib.quote(url_path, '')
    outfile = "%s/%s" % (workdir, escaped_path)
    lockfd = getlock(outfile)
    if lockfd:
        ui.debug("Writing mirror trigger to %s\n" % outfile)
        outf = file(outfile, "w")
        if(outf):
            print >> outf, kwargs['node']
            outf.close()
        else:
            print "Oh no, I couldn't open %s" % outfile
    else:
        print "Crap. Couldn't lock %s" % outfile
    unlock(outfile, lockfd)
