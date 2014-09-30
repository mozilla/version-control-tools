# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

"""Shared Mercurial code related to authentication."""

import os
import platform

from mercurial import config, util
from mercurial.i18n import _


class BugzillaAuth(object):
    """Holds Bugzilla authentication credentials."""

    def __init__(self, userid=None, cookie=None, username=None, password=None):
        if userid:
            self._type = 'cookie'
        else:
            self._type = 'explicit'

        self.userid = userid
        self.cookie = cookie
        self.username = username
        self.password = password

def getbugzillaauth(ui, require=False):
    """Obtain Bugzilla authentication credentials from any possible source.

    This returns a BugzillaAuth instance on success or None on failure.

    TODO: Incorporate bzexport's code for grabbing credentials from Firefox
    profiles.
    """

    username = ui.config('bugzilla', 'username')
    password = ui.config('bugzilla', 'password')

    if username and password:
        return BugzillaAuth(username=username, password=password)

    ui.warn(_('tip: to not prompt for Bugzilla credentials in the future, '
              'store them in your hgrc under bugzilla.username and '
              'bugzilla.password\n'))

    if not username:
        username = ui.prompt(_('Bugzilla username:'), None)

    if not password:
        password = ui.getpass(_('Bugzilla password:'), None)

    if username and password:
        return BugzillaAuth(username=username, password=password)

    if require:
        raise util.Abort(_('unable to obtain Bugzilla authentication.'))

    return None

def find_profiles_path():
    """Find the path containing Firefox profiles.

    The location of Firefox profiles is OS dependent. This function handles the
    differences.
    """
    path = None
    if platform.system() == 'Darwin':
        from Carbon import Folder, Folders
        pathref = Folder.FSFindFolder(Folders.kUserDomain,
                                      Folders.kApplicationSupportFolderType,
                                      Folders.kDontCreateFolder)
        basepath = pathref.FSRefMakePath()
        path = os.path.join(basepath, 'Firefox')
    elif platform.system() == 'Windows':
        # From http://msdn.microsoft.com/en-us/library/windows/desktop/bb762494%28v=vs.85%29.aspx
        CSIDL_APPDATA = 26
        path = win_get_folder_path(CSIDL_APPDATA)
        if path:
            path = os.path.join(path, 'Mozilla', 'Firefox')
    else:
        # Assume POSIX
        # Pretty simple in comparison, eh?
        path = os.path.expanduser('~/.mozilla/firefox')

    return path

def find_profile(name=None):
    """Find the location of a Firefox profile.

    This function attempts to locate a Firefox profile directory. It accepts
    the name of a profile to look for.

    Returns the path to a profile directory or None if no profile could be
    found.
    """
    path = find_profiles_path()
    if path is None:
        raise util.Abort(_('Could not find a Firefox profile'))

    profileini = os.path.join(path, 'profiles.ini')
    c = config.config()
    c.read(profileini)

    if name:
        sections = [s for s in c.sections() if name in [s, c.get(s, 'Name', None)]]
    else:
        sections = [s for s in c.sections() if c.get(s, 'Default', None)]
        if not sections:
            sections = c.sections()

    sections = [s for s in sections if c.get(s, 'Path', None) is not None]
    if not sections:
        raise util.Abort(_('Could not find a Firefox profile'))

    section = sections.pop(0)
    profile = c[section].get('Path')
    if c.get(section, 'IsRelative', '0') == '1':
        profile = os.path.join(path, profile)

    return profile

def win_get_folder_path(folder):
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


