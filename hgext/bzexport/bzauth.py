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
import urllib
import urllib2
import json
from mercurial import config, demandimport, util
from mercurial.i18n import _
try:
    import cPickle as pickle
except:
    import pickle
import bz

# requests doesn't like lazy importing
demandimport.disable()
import requests
demandimport.enable()

from mozhg.auth import (
    getbugzillaauth,
    win_get_folder_path,
)

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

    def __init__(self, url, userid=None, cookie=None, username=None, password=None):
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

        self._url = url.rstrip('/')
        self._session = None

    def auth(self):
        if self._type == self.typeCookie:
            return "userid=%s&cookie=%s" % (self._userid, self._cookie)
        else:
            return "username=%s&password=%s" % (urllib.quote(self._username), urllib.quote(self._password))

    def username(self, api_server):
        # This returns and caches the email-address-like username of the user's ID
        if self._type == self.typeCookie and self._username is None:
            return get_username(api_server, self)
        else:
            return self._username

    @property
    def session(self):
        """Obtain a ``requests.Session`` used for making requests."""
        if self._session:
            return self._session

        s = requests.Session()
        s.headers['User-Agent'] = 'bzexport'

        if self._type == self.typeCookie:
            s.cookies['Bugzilla_login'] = self._userid
            s.cookies['Bugzilla_logincookie'] = self._cookie
        else:
            # Resolve a token.
            params = {'login': self._username, 'password': self._password}
            res = s.get('%s/rest/login' % self._url, params=params)
            j = res.json()
            if 'token' not in j:
                raise util.Abort(_('failed to login to Bugzilla'))

            s.params['token'] = j['token']

        s.headers['Content-Type'] = 'application/json'
        s.headers['Accept'] = 'application/json'

        self._session = s
        return s

    def rest_request(self, method, path, data=None, **kwargs):
        """Make a request against the REST API.

        Returns the parsed JSON response as an object or raises if an error
        occurred.
        """
        url = '%s/rest/%s' % (self._url, path.lstrip('/'))
        if data:
            data = json.dumps(data)

        res = self.session.request(method, url, data=data, **kwargs)

        j = res.json()
        if 'error' in j:
            raise Exception('REST error on %s to %s: %s' % (
                method, url, j['message']))

        return j


def get_global_path(filename):
    path = None
    if platform.system() == "Windows":
        # The Windows user profile directory, eg: C:\Users\username
        # From http://msdn.microsoft.com/en-us/library/windows/desktop/bb762494%28v=vs.85%29.aspx
        CSIDL_PROFILE = 40
        path = win_get_folder_path(CSIDL_PROFILE)
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
    if global_cache:
        return global_cache

    cache_file = get_global_path(filename)

    try:
        fp = open(cache_file, "rb")
        global_cache = pickle.load(fp)
    except IOError, e:
        global_cache = {api_server: {'real_names': {}}}
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
    fp = open(user_cache, "a")
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
        cache['configuration'] = json.load(urllib2.urlopen(bz.get_configuration(api_server), timeout=30))
    except Exception, e:
        raise util.Abort("Error loading bugzilla configuration: " + str(e))

    cache['configuration_timestamp'] = now
    store_global_cache(filename)
    return cache['configuration']


def get_auth(ui, bugzilla, profile):
    auth = getbugzillaauth(ui, require=True)
    if auth.userid:
        return bzAuth(bugzilla, userid=auth.userid, cookie=auth.cookie)
    return bzAuth(bugzilla, username=auth.username, password=auth.password)


def get_username(api_server, token):
    req = bz.get_user(api_server, token)
    try:
        user = json.load(urllib2.urlopen(req, timeout=30))
        return user["name"]
    except urllib2.HTTPError, e:
        msg = ''
        try:
            err = json.load(e)
            msg = err['message']
        except:
            msg = e
            pass

        if msg:
            raise util.Abort('Unable to get username: %s\n' % msg)
        raise
    except Exception, e:
        raise util.Abort(_("Unable to get username: %s") % str(e))
