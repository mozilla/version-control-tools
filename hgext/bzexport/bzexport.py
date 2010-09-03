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

"""
bzexport

Attach a patch from a HG repository to a bugzilla bug.

To enable this extension, edit your ~/.hgrc (or %APPDATA%/Mercurial.ini)
and add:
[extensions]
bzexport = /path/to/bzexport.py

You can then use it like so:
hg bzexport REV BUG

Where REV is any local revision, and BUG is a bug number on
bugzilla.mozilla.org. The extension is tuned to work best with MQ
changesets (it can only currently work with applied patches).

If no revision is specified, it will default to 'tip'. If no
bug is specified, the changeset commit message will be scanned
for a bug number to use.

"""
from mercurial.i18n import _
from mercurial import commands, config, cmdutil, hg, node, util
from hgext import mq
import base64
from cStringIO import StringIO
import json
import os
import platform
import re
import shutil
import sqlite3
import tempfile
import urllib2
import urlparse

# This is stolen from buglink.py
bug_re = re.compile(r'''# bug followed by any sequence of numbers, or
                        # a standalone sequence of numbers
                     (
                        (?:
                          bug |
                          b= |
                          # a sequence of 5+ numbers preceded by whitespace
                          (?=\b\#?\d{5,}) |
                          # numbers at the very beginning
                          ^(?=\d)
                        )
                        (?:\s*\#?)(\d+)
                     )''', re.I | re.X)
review_re = re.compile(r'r[=?]([^ ]+)')

def create_attachment(api_server, userid, cookie, bug,
                      attachment_contents, description="attachment",
                      filename="attachment"):
    """
    Post an attachment to a bugzilla bug using BzAPI.

    """
    attachment = base64.b64encode(attachment_contents)
    url = api_server + "bug/%s/attachment?userid=%s&cookie=%s" % (bug, userid, cookie)
    # 'comments': [{'text': '...'}]
    # 'flags': [...]
    attachment_json = json.dumps({'data': attachment,
                                  'encoding': 'base64',
                                  'file_name': filename,
                                  'description': description,
                                  'is_patch': True,
                                  'content_type': 'text/plain'})
    req = urllib2.Request(url, attachment_json,
                          {"Accept": "application/json",
                           "Content-Type": "application/json"})
    conn = urllib2.urlopen(req)
    return conn.read()

def find_profile(ui):
    """
    Find the default Firefox profile location. Returns None
    if no profile could be located.

    """
    path = None
    if platform.system() == "Darwin":
        # Use FSFindFolder
        from Carbon import Folder, Folders
        pathref = Folder.FSFindFolder(Folders.kUserDomain,
                                      Folders.kApplicationSupportFolderType,
                                      Folders.kDontCreateFolder)
        basepath = path.FSRefMakePath()
        path = os.path.join(basepath, "Firefox")
    elif platform.system() == "Windows":
        # Use SHGetFolderPath
        import ctypes
        SHGetFolderPath = ctypes.windll.shell32.SHGetFolderPathW
        SHGetFolderPath.argtypes = [ctypes.c_void_p,
                                    ctypes.c_int,
                                    ctypes.c_void_p,
                                    ctypes.c_int32,
                                    ctypes.c_wchar_p]
        CSIDL_APPDATA = 26
        path_buf = ctypes.create_unicode_buffer(1024)
        if SHGetFolderPath(0, CSIDL_APPDATA, 0, 0, path_buf) == 0:
            path = os.path.join(path_buf.value, "Mozilla", "Firefox")
    else: # Assume POSIX
        # Pretty simple in comparison, eh?
        path = os.path.expanduser("~/.mozilla/firefox")
    if path is None:
        ui.write_err("Couldn't find a Firefox profile\n")
        return None

    profileini = os.path.join(path, "profiles.ini")
    c = config.config()
    c.read(profileini)
    profile = None
    for section in c.sections():
        if section == "General":
            continue
        if c.get(section, "Default", None) is not None or profile is None:
            profile = c.get(section, "Path", None)
            if c.get(section, "IsRelative", "0") == "1":
                profile = os.path.join(path, profile)
    if profile is None:
        ui.write_err("Couldn't find a Firefox profile\n")
        return None
    return profile

def get_cookies_from_profile(ui, profile, bugzilla):
    """
    Given a Firefox profile, try to find the login cookies
    for the given bugzilla URL.

    """
    cookies = os.path.join(profile, "cookies.sqlite")
    if not os.path.exists(cookies):
        return None, None

    # Get bugzilla hostname
    host = urlparse.urlparse(bugzilla).hostname

    # Firefox locks this file, so if we can't open it (browser is running)
    # then copy it somewhere else and try to open it.
    tempdir = None
    try:
        tempdir = tempfile.mkdtemp()
        tempcookies = os.path.join(tempdir, "cookies.sqlite")
        shutil.copyfile(cookies, tempcookies)
        conn = sqlite3.connect(tempcookies)
        login = conn.execute("select value from moz_cookies where name = 'Bugzilla_login' and host = ?", (host,)).fetchone()[0]
        cookie = conn.execute("select value from moz_cookies where name = 'Bugzilla_logincookie' and host = ?", (host,)).fetchone()[0]
        if isinstance(login, unicode):
            login = login.encode("utf-8")
            cookie = cookie.encode("utf-8")
        return login, cookie
    except Exception, e:
        ui.write_err("Failed to get bugzilla login cookies from "
                     "Firefox profile: %s\n" % str(e))
        return None, None
    finally:
        if tempdir:
            shutil.rmtree(tempdir)

def bzexport(ui, repo, *args, **opts):
    """
    Export changesets to bugzilla attachments.

    """
    api_server = ui.config("bzexport", "api_server", "https://api-dev.bugzilla.mozilla.org/0.6.1/")
    bugzilla = ui.config("bzexport", "bugzilla", "https://bugzilla.mozilla.org/")
    #TODO: allow overriding profile location via config
    #TODO: cache cookies?
    profile = find_profile(ui)
    if profile is None:
        return
    userid, cookie = get_cookies_from_profile(ui, profile, bugzilla)
    if userid is None or cookie is None:
        ui.write_err("Couldn't find bugzilla login cookies\n")
        return

    rev = None
    bug = None
    if len(args) < 2:
        # We need to guess at some args.
        if len(args) == 1:
            # Just one arg. Could be a revision or a bug number.
            # Check this first, because a series of digits
            # can be a revision number, but it's unlikely a user
            # would use it to mean a revision here.
            if not args[0].isdigit() and args[0] in repo:
                # Looks like a changeset
                rev = args[0]
            else:
                # Don't do any validation here, to allow
                # users to use bug aliases. The BzAPI call
                # will fail with bad bug numbers.
                bug = args[0]

        # With zero args we'll guess at both, and if we fail we'll
        # fail later.
    elif len(args) > 2:
        ui.write_error("Too many arguments to bzexport!\n")
        return
    else:
        # Just right.
        rev, bug = args

    if rev is None:
        # Default to 'tip'
        rev = 'tip'
        # But look for a nicer name in the MQ.
        if hasattr(repo, 'mq') and repo.mq.applied:
            rev = repo.mq.applied[-1].name

    contents = StringIO()
    cmdutil.export(repo, [rev], fp=contents)

    # Just always use the rev name as the patch name. Doesn't matter much.
    filename = rev

    #TODO: support --description= arg
    desc = repo[rev].description()
    if desc.startswith('[mq]'):
        desc = ui.prompt(_("Patch description:"), default=filename)
    else:
        # Lightly reformat changeset messages into attachment descriptions.
        # First, strip off any leading "bug NNN" or "b=NNN",
        # but save it in case a bug number was not provided.
        bzexport.newbug = None
        def dosub(m):
            bzexport.newbug = m.group(2)
            return ''
        desc = bug_re.sub(dosub, desc)
        if bzexport.newbug:
            if bug and bug != bzexport.newbug:
                ui.warn("Warning: Bug number %s from commandline doesn't match "
                        "bug number %s from changeset description\n"
                        % (bug, bzexport.newbug))
            else:
                bug = bzexport.newbug

        # Next strip any remaining leading dash with whitespace,
        # if the original was "bug NNN - "
        desc = desc.lstrip()
        if desc[0] == '-':
            desc = desc[1:].lstrip()

        # Next strip off review annotations
        #TODO: auto-convert these into review requests? Probably not
        # very helpful unless a unique string is provided.
        desc = review_re.sub('', desc).rstrip()

        # Finally, just take the first line in case there's a really long
        # changeset message.
        #TODO: add really long changeset messages as comments?
        if '\n' in desc:
            desc = desc.split('\n')[0]

    if bug is None:
        ui.write_err("Error: no bug number specified and no bug number "
                     "listed in changeset message!\n")
        return

    #TODO: support a --new argument for filing a new bug with a patch
    #TODO: support a --review=reviewers argument
    #TODO: support adding a comment along with the patch
    #TODO: support obsoleting old attachments (maybe intelligently?)
    try:
        result = json.loads(create_attachment(api_server, userid, cookie,
                                              bug, contents.getvalue(),
                                              filename=filename,
                                              description=desc))
        attachment_url = urlparse.urljoin(bugzilla,
                                          "attachment.cgi?id=" + result["id"] + "&action=edit")
        print "%s uploaded as %s" % (rev, attachment_url)
    except Exception, e:
        ui.write_err(_("Error sending patch: %s\n" % str(e)))

cmdtable = {
    'bzexport':
        (bzexport, [],
        _('hg bzexport [REV] [BUG]')),
}
