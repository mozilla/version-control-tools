# Copyright (C) 2010 Mozilla Foundation
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

# This script imports data from the older flat-file pushlog format,
# and the newer sqlite pushlog format into a newer sqlite schema.
#
# Unfortunately, when changing between the older format and the db,
# the semantics changed somewhat. The older format used to record the
# *HEAD* revision as of a push, but the db records the *first* changeset
# in a group of pushed changes. To make life simpler, the new schema
# will record all changesets for a push, but we need to migrate the old data
# over.
# To do so, we grab all logged pushes from the old log and the db,
# and then for each logged push, if it is in the old log, then it's a head,
# so store all changes since the previous push with this push. Otherwise,
# it's a 'first changeset', so store all changes up until the next push
# with this push. At the end we'll have one entry in the new pushlog
# table for every push, and one entry per-changeset in the changesets
# table, mapped back to the pushlog table.

try:
    import sqlite3 as sqlite
except ImportError:
    from pysqlite2 import dbapi2 as sqlite

import sys
import os.path
import re
from datetime import datetime
import time
from calendar import timegm
from rfc822 import parsedate_tz, mktime_tz
from mercurial import ui, hg
from mercurial.node import hex

reader = re.compile(r'^"([a-f0-9]{40})"\t"([^\t]*)"\t"([^\t]*)"$')
def readlog(logfile):
    """Read a pushlog and yield (node, user, date) for each line. Returns
    all the entries in chronological order. |date| is a timestamp."""
    try:
        fd = open(logfile)
    except IOError:
        return []
    entries = []
    for line in fd:
        (node, user, date) = reader.match(line).group(1, 2, 3)
        entries.append((node, user, mktime_tz(parsedate_tz(date))))
    fd.close()
    return entries

def readpushdb(pushdb):
    """Read a pushlog db and yield (node, user, date) for each line. Returns
    all the entries in chronological order. |date| is a timestamp."""
    try:
        conn = sqlite.connect(pushdb)
        entries = []
        res = conn.execute("SELECT node, user, date FROM pushlog ORDER BY date ASC")
        for (node, user, date) in res:
            entries.append((node, user, timegm(time.strptime(date, "%Y-%m-%dT%H:%M:%SZ"))))
        return entries
    except:
        return []

def nodeindb(pushdb, node):
    return pushdb.execute("SELECT COUNT(*) from changesets WHERE node = ?", (node,)) == 1

if len(sys.argv) != 2:
    print >>sys.stderr, "Must specify a repository as the only parameter (/path/to/repo/)"
    sys.exit(1)

### Main entrypoint

repo_path = os.path.abspath(sys.argv[1])
if not os.path.exists(repo_path):
    print >>sys.stderr, "Must specify a repository as the only parameter (/path/to/repo/)"
    sys.exit(1)

try:
    repo = hg.repository(ui.ui(), repo_path)
except:
    print >>sys.stderr, "Must specify a repository as the only parameter (/path/to/repo/)"
    sys.exit(1)

# we need to read both the old text pushlog
pushlog = os.path.join(repo_path, ".hg", "pushlog")
# ... and the newer pushlog db
oldpushdb = pushlog + ".db"
# and we're going to migrate them both to a new schema
pushdb = pushlog + "2.db"

# Open or create our new db
conn = sqlite.connect(pushdb)
conn.execute("CREATE TABLE IF NOT EXISTS changesets (pushid INTEGER, rev INTEGER, node text)")
conn.execute("CREATE TABLE IF NOT EXISTS pushlog (id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT, date INTEGER)")
conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS changeset_node ON changesets (node)")
conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS changeset_rev ON changesets (rev)")
conn.execute("CREATE INDEX IF NOT EXISTS pushlog_date ON pushlog (date)")
conn.execute("CREATE INDEX IF NOT EXISTS pushlog_user ON pushlog (user)")

# Read all entries from both pushlogs
flatlogentries = readlog(pushlog)
flatnodes = dict()
# dict for easy lookup of nodes
for (node, user, date) in flatlogentries:
    flatnodes[node] = 1
logentries = readpushdb(oldpushdb)
if len(logentries) == 0:
    # just in case someone is importing from an old flatfile log
    logentries = flatlogentries

# sort by revision #, just in case we have two pushes with the same date
logentries = [(node, repo.changectx(node), user, date) for (node,user,date) in logentries]
logentries.sort(lambda a,b: cmp(a[1].rev(),b[1].rev()))

# start at the beginning
lastrev = -1
next = 0
for (node, ctx, user, date) in logentries:
    next += 1
    if nodeindb(conn, node):
        # already in the database, move along
        lastrev = ctx.rev()
        continue
    res = conn.execute("INSERT INTO pushlog (user, date) VALUES(?,?)",
                       (user, date))
    pushid = res.lastrowid
    # insert this change first
    conn.execute("INSERT INTO changesets (pushid,rev,node) VALUES(?,?,?)",
                 (pushid, ctx.rev(), node))
    if node in flatnodes:
        # this was a HEAD revision, see if any other changes were pushed
        # along with it
        if lastrev != ctx.rev() - 1:
            for i in range(lastrev+1, ctx.rev()):
                c = repo.changectx(i)
                conn.execute("INSERT INTO changesets (pushid,rev,node) VALUES(?,?,?)",
                 (pushid, c.rev(), hex(c.node())))
        lastrev = ctx.rev()
    else:
        # this was the first change in a set of changes pushed, see
        # if any other changes were pushed along with it
        if next < len(logentries):
            nextctx = repo.changectx(logentries[next][0])
            if ctx.rev() + 1 != nextctx.rev():
                for i in range(ctx.rev()+1, nextctx.rev()):
                    c = repo.changectx(i)
                    conn.execute("INSERT INTO changesets (pushid,rev,node) VALUES(?,?,?)",
                                 (pushid, c.rev(), hex(c.node())))
                    lastrev = c.rev()
        else: # end of the list, see if we're missing any changes to tip
            if not 'tip' in ctx.tags():
                tip =  repo.changectx('tip')
                # we want everything up to and including tip
                for i in range(ctx.rev()+1, tip.rev()+1):
                    c = repo.changectx(i)
                    conn.execute("INSERT INTO changesets (pushid,rev,node) VALUES(?,?,?)",
                                 (pushid, c.rev(), hex(c.node())))
                    lastrev = c.rev()

conn.commit()
