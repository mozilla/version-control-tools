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

import os
import platform
import time
import tempfile
import shutil
import urlparse
import sqlite3
import urllib2
import json
from mercurial import config, util
from mercurial.i18n import _
try:
  import cPickle as pickle
except:
  import pickle
import bz

global_cache = None

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

    def username(self, api_server):
        # This returns and caches the email-address-like username of the user's ID
        if self._type == self.typeCookie and self._username is None:
            return get_username(api_server, self)
        else:
            return self._username

def get_global_path(filename):
    path = None
    if platform.system() == "Windows":
        CSIDL_PERSONAL = 5
        path = win_get_folder_path(CSIDL_PERSONAL)
    else:
        path = os.path.expanduser("~")
    if path:
        path = os.path.join(path, filename)
    return path

def store_global_cache(filename):
    fp = open(get_global_path(filename), "wb")
    pickle.dump(global_cache, fp)
    fp.close()

def load_global_cache(ui, api_server, filename):
    global global_cache
    cache_file = get_global_path(filename)

    try:
        fp = open(cache_file, "rb");
        global_cache = pickle.load(fp)
    except IOError, e:
        global_cache = { api_server: { 'real_names': {} } }
    except Exception, e:
        raise util.Abort("Error loading user cache: " + str(e))

    return global_cache

def store_user_cache(cache, filename):
    user_cache = get_global_path(filename)
    fp = open(user_cache, "wb")
    for section in cache.sections():
        fp.write("[" + section + "]\n")
        for (user, name) in cache.items(section):
            fp.write(user + " = " + name + "\n")
        fp.write("\n")
    fp.close()

def load_user_cache(ui, api_server, filename):
    user_cache = get_global_path(filename)

    # Ensure that the cache exists before attempting to use it
    fp = open(user_cache, "a");
    fp.close()

    c = config.config()
    c.read(user_cache)
    return c

def load_configuration(ui, api_server, filename):
    global_cache = load_global_cache(ui, api_server, filename)
    cache = {}
    try:
        cache = global_cache[api_server]
    except:
        global_cache[api_server] = cache
    now = time.time()
    if cache.get('configuration', None) and now - cache['configuration_timestamp'] < 24*60*60*7:
        return cache['configuration']

    ui.write("Refreshing configuration cache for " + api_server + "\n")
    try:
        cache['configuration'] = json.load(urllib2.urlopen(bz.get_configuration(api_server)))
    except Exception, e:
        raise util.Abort("Error loading bugzilla configuration: " + str(e))

    cache['configuration_timestamp'] = now
    store_global_cache(filename)
    return cache['configuration']

def win_get_folder_path(folder):
    # Use SHGetFolderPath
    import ctypes
    SHGetFolderPath = ctypes.windll.shell32.SHGetFolderPathW
    SHGetFolderPath.argtypes = [ctypes.c_void_p,
                                ctypes.c_int,
                                ctypes.c_void_p,
                                ctypes.c_int32,
                                ctypes.c_wchar_p]
    path_buf = ctypes.create_unicode_buffer(1024)
    if SHGetFolderPath(0, folder, 0, 0, path_buf) != 0:
        return None

    return path_buf.value

def find_profile(ui, profileName):
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
        CSIDL_APPDATA = 26
        path = win_get_folder_path(CSIDL_APPDATA)
        if path:
            path = os.path.join(path, "Mozilla", "Firefox")
    else: # Assume POSIX
        # Pretty simple in comparison, eh?
        path = os.path.expanduser("~/.mozilla/firefox")
    if path is None:
        raise util.Abort(_("Could not find a Firefox profile"))

    profileini = os.path.join(path, "profiles.ini")
    c = config.config()
    c.read(profileini)

    if profileName:
        sections = [ s for s in c.sections() if profileName in [ s, c.get(s, "Name", None) ] ]
    else:
        sections = [ s for s in c.sections() if c.get(s, "Default", None) ]
        if len(sections) == 0:
            sections = c.sections()

    sections = [ s for s in sections if c.get(s, "Path", None) is not None ]
    if len(sections) == 0:
        raise util.Abort(_("Could not find a Firefox profile"))

    section = sections.pop(0)
    profile = c[section].get("Path")
    if c.get(section, "IsRelative", "0") == "1":
        profile = os.path.join(path, profile)
    return profile

# Choose the cookie to use based on how much of its path matches the URL.
# Useful if you happen to have cookies for both
# https://landfill.bugzilla.org/bzapi_sandbox/ and
# https://landfill.bugzilla.org/bugzilla-3.6-branch/, for example.
def matching_path_len(cookie_path, url_path):
    return len(cookie_path) if url_path.startswith(cookie_path) else 0

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
    path = urlparse.urlparse(bugzilla).path

    # Firefox locks this file, so if we can't open it (browser is running)
    # then copy it somewhere else and try to open it.
    tempdir = None
    try:
        tempdir = tempfile.mkdtemp()
        tempcookies = os.path.join(tempdir, "cookies.sqlite")
        shutil.copyfile(cookies, tempcookies)
        # Firefox uses sqlite's WAL feature, which bumps the sqlite
        # version number. Older sqlites will refuse to open the db,
        # but the actual format is the same (just the journalling is different).
        # Patch the file to give it an older version number so we can open it.
        with open(tempcookies, 'r+b') as f:
            f.seek(18, 0)
            f.write("\x01\x01")
        conn = sqlite3.connect(tempcookies)
        logins = conn.execute("select value, path from moz_cookies where name = 'Bugzilla_login' and (host = ? or host = ?)", (host, "." + host)).fetchall()
        row = sorted(logins, key = lambda row: -matching_path_len(row[1], path))[0]
        login = row[0]
        cookie = conn.execute("select value from moz_cookies "
                              "where name = 'Bugzilla_logincookie' "
                              " and (host = ? or host= ?) "
                              " and path = ?",
                              (host, "." + host, row[1])).fetchone()[0]
        ui.debug("host=%s path=%s login=%s cookie=%s\n" % (host, row[1], login, cookie))
        if isinstance(login, unicode):
            login = login.encode("utf-8")
            cookie = cookie.encode("utf-8")
        return login, cookie

    except Exception, e:
        if not isinstance(e, IndexError):
            ui.write_err(_("Failed to get bugzilla login cookies from "
                           "Firefox profile at %s: %s") % (profile, str(e)))
        pass

    finally:
        if tempdir:
            shutil.rmtree(tempdir)

def get_auth(ui, bugzilla, profile, username, password):
    userid = None
    cookie = None

    if not password:
        profile = find_profile(ui, profile)
        if profile:
            try:
                userid, cookie = get_cookies_from_profile(ui, profile, bugzilla)
            except Exception, e:
                print("Warning: " + str(e))
                pass

        if cookie:
            username = None # might not match userid
        else:
            ui.write("No bugzilla login cookies found in profile.\n")
            if not username:
                username = ui.prompt("Enter username for %s:" % bugzilla)
            if not password:
                password = ui.getpass("Enter password for %s: " % username)

    return bzAuth(userid, cookie, username, password)

def get_username(api_server, token):
    req = bz.get_user(api_server, token)
    try:
        user = json.load(urllib2.urlopen(req))
        return user["name"]
    except Exception, e:
        raise util.Abort(_("Unable to get username: %s") % str(e))
