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
from mercurial import commands, config, cmdutil, hg, node, util, patch
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
import urllib
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
review_re = re.compile(r'[ra][=?]([^ ]+)')

def urlopen(ui, req):
    """Wraps urllib2.urlopen() to provide error handling."""
    ui.debug('Requesting %s\n' % req.get_full_url())
    try:
        return urllib2.urlopen(req)
    except urllib2.HTTPError, e:
        try:
            err = json.load(e)
            msg = err['message']
        except:
            pass

        if msg:
            ui.warn('Error: %s\n' % msg)
        raise

class bzAuth:
    """
    A helper class to abstract away authentication details.  There are two
    allowable types of authentication: userid/cookie and username/password.
    We encapsulate it here so that functions that interact with bugzilla
    need only call the 'auth' method on the token to get a correct URL.
    """
    typeCookie = 1
    typeExplicit = 2
    def __init__(self, userid, cookie, username, password):
        assert (userid and cookie) or (username and password)
        assert not ((userid or cookie) and (username or password))
        if userid:
            self._type = self.typeCookie
            self._userid = userid
            self._cookie = cookie
            self._username = None
        else:
            self._type = self.typeExplicit
            self._username = username
            self._password = password

    def auth(self):
        if self._type == self.typeCookie:
            return "userid=%s&cookie=%s" % (self._userid, self._cookie)
        else:
            return "username=%s&password=%s" % (self._username, self._password)

    def username(self, ui, api_server):
        # This returns and caches the email-address-like username of the user's ID
        if self._type == self.typeCookie and self._username is None:
            url = api_server + "user/%s?%s" % (self._userid, self.auth())
            req = urllib2.Request(url, None,
                                  {"Accept": "application/json",
                                   "Content-Type": "application/json"})
            conn = urlopen(ui, req)
            try:
                user = json.load(conn)
            except Exception, e:
                pass
            if user and user["name"]:
                return user["name"]
            else:
                ui.write_err("Error: couldn't get your username: %s\n" % str(e))
                return None
        else:
            return self._username

def review_flag_type_id(ui, api_server):
    url = api_server + "configuration";
    req = urllib2.Request(url, None,
                          {"Accept": "application/json",
                           "Content-Type": "application/json"})
    conn = urlopen(ui, req)
    try:
        configuration = json.load(conn)
    except Exception, e:
        pass
    if configuration and configuration["flag_type"]:
        for flag_id, flag in configuration["flag_type"].iteritems():
            if flag["name"] == "review":
                return flag_id
    ui.write_err("Error: couldn't find review flag id: %s\n" % str(e))
    return None

def create_attachment(ui, api_server, token, bug,
                      attachment_contents, description="attachment",
                      filename="attachment", comment="", reviewers=None):
    """
    Post an attachment to a bugzilla bug using BzAPI.

    """
    attachment = base64.b64encode(attachment_contents)
    url = api_server + "bug/%s/attachment?%s" % (bug, token.auth())

    json_data = {'data': attachment,
                 'encoding': 'base64',
                 'file_name': filename,
                 'description': description,
                 'is_patch': True,
                 'content_type': 'text/plain'}
    if reviewers is not None:
        flag_type_id = review_flag_type_id(ui, api_server)
        flags = []
        flags.append({"name": "review",
                      "requestee": {"name": ", ".join(reviewers)},
                      "setter": {"name": token.username(ui, api_server)},
                      "status": "?",
                      "type_id": flag_type_id})
        json_data["flags"] = flags
    if comment:
        json_data["comments"] = [{'text': comment}]

    attachment_json = json.dumps(json_data)
    req = urllib2.Request(url, attachment_json,
                          {"Accept": "application/json",
                           "Content-Type": "application/json"})
    conn = urlopen(ui, req)
    return conn

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
        basepath = pathref.FSRefMakePath()
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
        ui.write_err("Error: couldn't find a Firefox profile.\n")
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
        ui.write_err("Error: couldn't find a Firefox profile.\n")
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
        login = conn.execute("select value from moz_cookies where name = 'Bugzilla_login' and (host = ? or host = ?)", (host, "." + host)).fetchone()[0]
        cookie = conn.execute("select value from moz_cookies where name = 'Bugzilla_logincookie' and (host = ? or host= ?)", (host, "." + host)).fetchone()[0]
        if isinstance(login, unicode):
            login = login.encode("utf-8")
            cookie = cookie.encode("utf-8")
        return login, cookie
    except Exception, e:
        ui.write_err("Error: failed to get bugzilla login cookies from "
                     "Firefox profile at %s: %s\n" % (profile, str(e)))
        return None, None
    finally:
        if tempdir:
            shutil.rmtree(tempdir)

class PUTRequest(urllib2.Request):
    def get_method(self):
        return "PUT"

def obsolete_old_patches(ui, api_server, token, bug, filename, ignore_id):
    url = api_server + "bug/%s/attachment?%s" % (bug, token.auth()) 
    req = urllib2.Request(url, None,
                          {"Accept": "application/json",
                           "Content-Type": "application/json"})
    conn = urlopen(ui, req)
    try:
        bug = json.load(conn)
    except Exception, e:
        ui.write_err("Error: couldn't load info for bug " + bug + ": %s\n" % str(e))
        return False

    patches = [p for p in bug["attachments"] if p["is_patch"] and not p["is_obsolete"] and p["file_name"] == filename and int(p["id"]) != int(ignore_id)]
    if not len(patches):
        return True

    for p in patches:
        #TODO: "?last_change_time=" + p["last_change_time"] to avoid conflicts?
        url = api_server + "attachment/%s?%s" % (str(p["id"]), token.auth())

        attachment_data = p
        attachment_data["is_obsolete"] = True
        attachment_json = json.dumps(attachment_data)
        req = PUTRequest(url, attachment_json,
                         {"Accept": "application/json",
                          "Content-Type": "application/json"})
        conn = urlopen(ui, req)
        try:
            result = json.load(conn)
        except Exception, e:
            ui.write_err("Error: couldn't update attachment " + p["id"] + ": %s\n" % e)
            return False

    return True

def find_reviewers(ui, api_server, token, search_strings):
    search_results = []
    for search_string in search_strings:
        url = api_server + "user?match=%s&%s" % (search_string, token.auth()) 
        try:
            req = urllib2.Request(url, None,
                                  {"Accept": "application/json",
                                   "Content-Type": "application/json"})
            conn = urlopen(ui, req)
            users = json.load(conn)
            error = None
            name = None
            real_names = map(lambda user: "%s <%s>" % (user["real_name"], user["email"]) if user["real_name"] else user["email"], users["users"])
            names = map(lambda user: user["name"], users["users"])
            search_results.append({"search_string": search_string,
                                   "names": names,
                                   "real_names": real_names})
        except Exception, e:
            search_results.append({"search_string": search_string,
                                   "error": str(e),
                                   "real_names": None})
            raise
    return search_results

def bzexport(ui, repo, *args, **opts):
    """
    Export changesets to bugzilla attachments.

    """
    api_server = ui.config("bzexport", "api_server", "https://api-dev.bugzilla.mozilla.org/latest/")
    bugzilla = ui.config("bzexport", "bugzilla", "https://bugzilla.mozilla.org/")
    username = ui.config("bzexport", "username", None)
    if username:
        username = urllib.quote(username)
    password = ui.config("bzexport", "password", None)
    if password:
        password = urllib.quote(password)
    userid = None
    cookie = None
    #TODO: allow overriding profile location via config
    #TODO: cache cookies?
    if not username:
        profile = find_profile(ui)
        if profile is None:
            return

        userid, cookie = get_cookies_from_profile(ui, profile, bugzilla)
        if userid is None or cookie is None:
            ui.write_err("Error: couldn't find bugzilla login cookies.\n")
            return

    auth = bzAuth(userid, cookie, username, password)

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
        ui.write_err("Too many arguments to bzexport!\n")
        return
    else:
        # Just right.
        rev, bug = args

    if rev is None:
        # Default to 'tip'
        rev = 'tip'

    if repo[rev] == repo["tip"]:
        m, a, r, d = repo.status()[:4]
        if (m or a or r or d):
            ui.write_err("Local changes found; refresh first!\n");
            return

    if rev in ["tip", "qtip"]:
        # Look for a nicer name in the MQ.
        if hasattr(repo, 'mq') and repo.mq.applied:
            rev = repo.mq.applied[-1].name

    contents = StringIO()
    diffopts = patch.diffopts(ui, opts)
    context = ui.config("bzexport", "unified", None)
    if context:
        diffopts.context = int(context)
    if hasattr(cmdutil, "export"):
        cmdutil.export(repo, [rev], fp=contents,
                       opts=diffopts)
    else:
        # Support older hg versions
        patch.export(repo, [rev], fp=contents,
                     opts=diffopts)

    # Just always use the rev name as the patch name. Doesn't matter much.
    filename = rev

    desc = opts['description'] or repo[rev].description()
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
        desc = bug_re.sub(dosub, desc, 1)
        if not bzexport.newbug:
            # Try to find it in the original revision description, if
            # it wasn't found in desc.
            bug_re.sub(dosub, repo[rev].description(), 1)
        if bzexport.newbug:
            if bug and bug != bzexport.newbug:
                ui.warn("Warning: Bug number %s from commandline doesn't match "
                        "bug number %s from changeset description\n"
                        % (bug, bzexport.newbug))
            else:
                bug = bzexport.newbug

        # Next strip any remaining leading separator with whitespace,
        # if the original was something like "bug NNN - "
        desc = desc.lstrip()
        if desc[0] in ['-', ':', '.']:
            desc = desc[1:].lstrip()

        # Next strip off review and approval annotations
        #TODO: auto-convert these into review requests? Probably not
        # very helpful unless a unique string is provided.
        desc = review_re.sub('', desc).rstrip()

        # Finally, just take the first line in case there's a really long
        # changeset message.
        #TODO: add really long changeset messages as comments?
        if '\n' in desc:
            desc = desc.split('\n')[0]

    if bug is None:
        ui.write_err("No bug number specified and no bug number "
                     "listed in changeset message!\n")
        return

    comment = ""
    if opts["comment"]:
        comment = opts["comment"]
    elif opts["edit_comment"]:
        comment = """

HG: Enter a comment to add to the bug with the attachment.
HG: Lines starting with 'HG:' will be removed.
"""
        comment = ui.edit(comment, ui.username())
        comment = re.sub("(?m)^HG:.*\n", "", comment)
        if not comment.strip():
            ui.write_err("Empty comment specified. Aborting!\n")
            return

    #TODO: support a --new argument for filing a new bug with a patch
    reviewers = None
    if opts["review"]:
        reviewers = []
        search_strings = opts["review"].split(",")
        search_results = find_reviewers(ui, api_server, auth, search_strings)
        search_failed = False
        for search_result in search_results:
            if search_result["real_names"] is None:
                ui.write_err("Error: couldn't search for user with search string \"%s\": %s\n" % (search_result["search_string"], search_result["error"]))
                search_failed = True
            elif len(search_result["real_names"]) > 5:
                ui.write_err("Error: too many bugzilla users matching \"%s\":\n\n" % search_result["search_string"])
                for real_name in search_result["real_names"]:
                    ui.write_err("  %s\n" % real_name.encode('ascii', 'replace'))
                search_failed = True
            elif len(search_result["real_names"]) > 1:
                prompts = []
                message = "Multiple bugzilla users matching \"%s\":\n\n" % search_result["search_string"]
                for i in range(len(search_result["real_names"])):
                    prompts.append("&%d" % (i + 1))
                    message += "  %d. %s\n" % (i + 1, search_result["real_names"][i].encode('ascii', 'replace'))
                prompts.append("&abort")
                message += "  a. Abort\n\nSelect reviewer:"
                choice = ui.promptchoice(message, prompts, len(prompts) - 1)
                if choice == len(prompts) - 1:
                    search_failed = True
                else:
                    reviewers.append(search_result["names"][choice])
            elif len(search_result["real_names"]) == 1:
                reviewers.append(search_result["names"][0])
            else:
                ui.write_err("Couldn't find a bugzilla user matching \"%s\"!\n" % search_result["search_string"])
                search_failed = True
        if search_failed:
            return

    result_id = None
    try:
        result = json.load(create_attachment(ui, api_server, auth,
                                             bug, contents.getvalue(),
                                             filename=filename,
                                             description=desc,
                                             comment=comment,
                                             reviewers=reviewers))
        attachment_url = urlparse.urljoin(bugzilla,
                                          "attachment.cgi?id=" + result["id"] + "&action=edit")
        print "%s uploaded as %s" % (rev, attachment_url)
        result_id = result["id"]

    except Exception, e:
        ui.write_err(_("Error sending patch: %s\n" % str(e)))

    if not result_id or not obsolete_old_patches(ui, api_server, auth, bug, filename, result_id):
        return

cmdtable = {
    'bzexport':
        (bzexport,
         [('d', 'description', '', 'Bugzilla attachment description'),
          ('c', 'comment', '', 'Comment to add with the attachment'),
          ('e', 'edit-comment', None,
           'Open a text editor to specify a comment to add with the attachment.'),
          ('r', 'review', '',
           'List of users to request review from (comma-separated search strings)')],
        _('hg bzexport [options] [REV] [BUG]')),
}
