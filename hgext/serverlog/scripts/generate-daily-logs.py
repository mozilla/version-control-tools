#!/usr/bin/env python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# Intended to be used in a CRON job to produce the per-day log files.

import datetime
import os
import subprocess


HERE = os.path.abspath(os.path.dirname(__file__))

now = datetime.datetime.utcnow()
today = now.date()
yesterday = today - datetime.timedelta(days=1)

relevant_logs = ['/var/log/hg.log']

old_log = '/var/log/hg-log-%s' % yesterday.strftime('%Y%m%d')
if os.path.exists(old_log):
    relevant_logs.insert(0, old_log)

dest_log = '/var/log/hg/parsed.%s' % yesterday.isoformat()

subprocess.check_call('cat %s | %s/parse.py --date %s > %s' % (
    ' '.join(relevant_logs), HERE, yesterday.isoformat(), dest_log),
    shell=True)

subprocess.check_call('cat %s | %s/totals-by-day.py > /var/log/hg/totals-by-day.%s' % (
    dest_log, HERE, yesterday.isoformat()),
    shell=True)

subprocess.check_call('cat %s | %s/repo-totals-by-day.py > /var/log/hg/repo-totals-by-day.%s' % (
    dest_log, HERE, yesterday.isoformat()),
    shell=True)
