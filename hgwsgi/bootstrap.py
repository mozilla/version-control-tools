# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

# This file contains common code that is executed by every hgweb.wsgi
# WSGI entrypoint.

import errno
import os

# Set this before importing mercurial.* modules.
os.environ["HGENCODING"] = "UTF-8"


from mercurial.hgweb import hgwebdir
from mercurial.hgweb import hgwebdir_mod_inner
from mercurial import error, pycompat

# Force the registration modules (template keywords, revsets, web commands,
# bundle2 part handlers, ...) to be imported and run at worker startup. Since
# Mercurial 7.2, modules register their items in small "inert" `tables` modules
# to break import cycles, and those tables are only populated as a side effect
# of *executing* the registering module's body. A worker can reach a code path
# (e.g. serving an archive download, which renders .hg_archival.txt) before the
# relevant module body has run, leaving its table empty -- for the archive case
# `latesttag` is unregistered and rendering 500s with
# "ParseError: '' is not iterable of mappings".
#
# mercurial.initialization.init() is the upstream-blessed entry point for this:
# it eagerly imports and runs every registration module. mercurial.hgweb.hgweb()
# calls it, but mercurial.hgweb.hgwebdir() -- which make_application() uses for
# the multi-repo view -- does not, so we call it ourselves here.
# Upstream: https://foss.heptapod.net/mercurial/mercurial-devel/-/work_items/10127
from mercurial import initialization

initialization.init()


def _compat_findrepos(orig):
    """Patch findrepos to restore pre-7.2 behaviour for missing repo paths.

    Mercurial 7.2 (c3b91e39df52) added strict validation that raises
    InputError when a configured repo path is not a valid repository. This
    patch catches that error per-path and includes the path in the routing
    anyway, matching pre-7.2 behaviour where absent repos were present in
    the routing and would simply 404 at open time.
    """
    def wrapper(paths):
        repos = []
        for name, path in paths:
            try:
                repos.extend(orig([(name, path)]))
            except error.InputError:
                repos.append((name.strip(b'/'), path))
        return repos
    return wrapper

hgwebdir_mod_inner.findrepos = _compat_findrepos(hgwebdir_mod_inner.findrepos)


# Set HTTPS_PROXY from /etc/environment value, if present. We don't
# source /etc/environment completely because we have no need for
# some of its variables. And HTTP_PROXY could confuse WSGI into
# thinking the client sent a "Proxy: " request header.
def set_env():
    try:
        with open("/etc/environment", "rb") as fh:
            for line in fh:
                if not line.startswith(b"HTTPS_PROXY="):
                    continue

                value = line.strip().split(b"=", 1)[1]
                value = value.strip(b'"')

                os.environ["HTTPS_PROXY"] = pycompat.strurl(value)
                break

    except IOError as e:
        if e.errno != errno.ENOENT:
            raise


def make_application(wsgi_dir):
    set_env()

    config = os.path.join(wsgi_dir, "hgweb.config")

    return hgwebdir(pycompat.bytestr(config))
