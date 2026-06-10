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

# Force-populate the template keyword/default-template registries at worker
# startup. Since Mercurial 7.2 (56da8902ae00, "cycle-breaking: get the
# template's keywords from `tables` in `formatter`"), templateformatter reads
# its default keywords from tables.template_keyword_table but no longer imports
# templatekw -- and that table is only populated as a side effect of *executing*
# templatekw (its @templatekeyword decorators run at module body execution).
# Under demandimport, a worker that serves an archive download before rendering
# any keyword-using page never executes templatekw, so `latesttag` is
# unregistered and .hg_archival.txt rendering 500s with
# "ParseError: '' is not iterable of mappings".
#
# NB: a plain `import templatekw` under demandimport only creates a lazy proxy
# and does NOT run the module body, so it would not populate the registry. Use
# demandimport.deactivated() to force a real, eager import here.
# Upstream: https://foss.heptapod.net/mercurial/mercurial-devel/-/work_items/10127
from mercurial import demandimport

with demandimport.deactivated():
    from mercurial import templatekw  # noqa: F401  (imported for its side effects)


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
