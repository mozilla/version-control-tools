try:
    import sqlite3 as sqlite
except ImportError:
    from pysqlite2 import dbapi2 as sqlite

import sys
import os.path
import re
from datetime import datetime
from rfc822 import parsedate_tz, mktime_tz

if len(sys.argv) != 2:
    print >>sys.stderr, "Must specify a pushlog file as the only parameter"
    sys.exit(1)

pushlog = sys.argv[1]
if not os.path.exists(pushlog):
    print >>sys.stderr, "Must specify a pushlog file as the only parameter"
    sys.exit(1)

pushlog = os.path.abspath(pushlog)
pushdb = pushlog + ".db"

conn = sqlite.connect(pushdb)
conn.execute("CREATE TABLE pushlog (node text, user text, date text)")
conn.execute("CREATE INDEX pushlog_date ON pushlog (date)")
conn.execute("CREATE INDEX pushlog_user ON pushlog (user)")

reader = re.compile(r'^"([a-f0-9]{40})"\t"([^\t]*)"\t"([^\t]*)"$')

def readlog(logfile):
    """Read a pushlog and yield (node, user, date) for each line."""
    fd = open(logfile)
    entries = []
    for line in fd:
        (node, user, date) = reader.match(line).group(1, 2, 3)
        # yeah, this is pretty awful. working with rfc822 dates sucks.
        d = datetime.utcfromtimestamp(mktime_tz(parsedate_tz(date)))
        entries.append((node, user, d.isoformat()+"Z"))
    entries.reverse()
    return entries

entries = readlog(pushlog)
conn.executemany("INSERT INTO pushlog (node, user, date) values(?,?,?)",
                 entries)
conn.commit()
