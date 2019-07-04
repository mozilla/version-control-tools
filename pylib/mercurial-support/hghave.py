from __future__ import absolute_import

import os
import re
import socket
import stat
import subprocess
import sys
import tempfile

tempprefix = 'hg-hghave-'

checks = {
    "true": (lambda: True, "yak shaving"),
    "false": (lambda: False, "nail clipper"),
}

try:
    import msvcrt
    msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
    msvcrt.setmode(sys.stderr.fileno(), os.O_BINARY)
except ImportError:
    pass

stdout = getattr(sys.stdout, 'buffer', sys.stdout)
stderr = getattr(sys.stderr, 'buffer', sys.stderr)

if sys.version_info[0] >= 3:
    def _bytespath(p):
        if p is None:
            return p
        return p.encode('utf-8')

    def _strpath(p):
        if p is None:
            return p
        return p.decode('utf-8')
else:
    def _bytespath(p):
        return p

    _strpath = _bytespath

def check(name, desc):
    """Registers a check function for a feature."""
    def decorator(func):
        checks[name] = (func, desc)
        return func
    return decorator

def checkvers(name, desc, vers):
    """Registers a check function for each of a series of versions.

    vers can be a list or an iterator"""
    def decorator(func):
        def funcv(v):
            def f():
                return func(v)
            return f
        for v in vers:
            v = str(v)
            f = funcv(v)
            checks['%s%s' % (name, v.replace('.', ''))] = (f, desc % v)
        return func
    return decorator

def checkfeatures(features):
    result = {
        'error': [],
        'missing': [],
        'skipped': [],
    }

    for feature in features:
        negate = feature.startswith('no-')
        if negate:
            feature = feature[3:]

        if feature not in checks:
            result['missing'].append(feature)
            continue

        check, desc = checks[feature]
        try:
            available = check()
        except Exception:
            result['error'].append('hghave check failed: %s' % feature)
            continue

        if not negate and not available:
            result['skipped'].append('missing feature: %s' % desc)
        elif negate and available:
            result['skipped'].append('system supports %s' % desc)

    return result

def require(features):
    """Require that features are available, exiting if not."""
    result = checkfeatures(features)

    for missing in result['missing']:
        stderr.write(('skipped: unknown feature: %s\n'
                      % missing).encode('utf-8'))
    for msg in result['skipped']:
        stderr.write(('skipped: %s\n' % msg).encode('utf-8'))
    for msg in result['error']:
        stderr.write(('%s\n' % msg).encode('utf-8'))

    if result['missing']:
        sys.exit(2)

    if result['skipped'] or result['error']:
        sys.exit(1)

def matchoutput(cmd, regexp, ignorestatus=False):
    """Return the match object if cmd executes successfully and its output
    is matched by the supplied regular expression.
    """
    r = re.compile(regexp)
    p = subprocess.Popen(
        cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    s = p.communicate()[0]
    ret = p.returncode
    return (ignorestatus or not ret) and r.search(s)

@check("baz", "GNU Arch baz client")
def has_baz():
    return matchoutput('baz --version 2>&1', br'baz Bazaar version')

@check("bzr", "Canonical's Bazaar client")
def has_bzr():
    try:
        import bzrlib
        import bzrlib.bzrdir
        import bzrlib.errors
        import bzrlib.revision
        import bzrlib.revisionspec
        bzrlib.revisionspec.RevisionSpec
        return bzrlib.__doc__ is not None
    except (AttributeError, ImportError):
        return False

@checkvers("bzr", "Canonical's Bazaar client >= %s", (1.14,))
def has_bzr_range(v):
    major, minor = v.split('rc')[0].split('.')[0:2]
    try:
        import bzrlib
        return (bzrlib.__doc__ is not None
                and bzrlib.version_info[:2] >= (int(major), int(minor)))
    except ImportError:
        return False

@check("chg", "running with chg")
def has_chg():
    return 'CHGHG' in os.environ

@check("cvs", "cvs client/server")
def has_cvs():
    re = br'Concurrent Versions System.*?server'
    return matchoutput('cvs --version 2>&1', re) and not has_msys()

@check("cvs112", "cvs client/server 1.12.* (not cvsnt)")
def has_cvs112():
    re = br'Concurrent Versions System \(CVS\) 1.12.*?server'
    return matchoutput('cvs --version 2>&1', re) and not has_msys()

@check("cvsnt", "cvsnt client/server")
def has_cvsnt():
    re = br'Concurrent Versions System \(CVSNT\) (\d+).(\d+).*\(client/server\)'
    return matchoutput('cvsnt --version 2>&1', re)

@check("darcs", "darcs client")
def has_darcs():
    return matchoutput('darcs --version', br'\b2\.([2-9]|\d{2})', True)

@check("mtn", "monotone client (>= 1.0)")
def has_mtn():
    return matchoutput('mtn --version', br'monotone', True) and not matchoutput(
        'mtn --version', br'monotone 0\.', True)

@check("eol-in-paths", "end-of-lines in paths")
def has_eol_in_paths():
    try:
        fd, path = tempfile.mkstemp(dir='.', prefix=tempprefix, suffix='\n\r')
        os.close(fd)
        os.remove(path)
        return True
    except (IOError, OSError):
        return False

@check("execbit", "executable bit")
def has_executablebit():
    try:
        EXECFLAGS = stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
        fh, fn = tempfile.mkstemp(dir='.', prefix=tempprefix)
        try:
            os.close(fh)
            m = os.stat(fn).st_mode & 0o777
            new_file_has_exec = m & EXECFLAGS
            os.chmod(fn, m ^ EXECFLAGS)
            exec_flags_cannot_flip = ((os.stat(fn).st_mode & 0o777) == m)
        finally:
            os.unlink(fn)
    except (IOError, OSError):
        # we don't care, the user probably won't be able to commit anyway
        return False
    return not (new_file_has_exec or exec_flags_cannot_flip)

@check("icasefs", "case insensitive file system")
def has_icasefs():
    # Stolen from mercurial.util
    fd, path = tempfile.mkstemp(dir='.', prefix=tempprefix)
    os.close(fd)
    try:
        s1 = os.stat(path)
        d, b = os.path.split(path)
        p2 = os.path.join(d, b.upper())
        if path == p2:
            p2 = os.path.join(d, b.lower())
        try:
            s2 = os.stat(p2)
            return s2 == s1
        except OSError:
            return False
    finally:
        os.remove(path)

@check("fifo", "named pipes")
def has_fifo():
    if getattr(os, "mkfifo", None) is None:
        return False
    name = tempfile.mktemp(dir='.', prefix=tempprefix)
    try:
        os.mkfifo(name)
        os.unlink(name)
        return True
    except OSError:
        return False

@check("killdaemons", 'killdaemons.py support')
def has_killdaemons():
    return True

@check("cacheable", "cacheable filesystem")
def has_cacheable_fs():
    from mercurial import util

    fd, path = tempfile.mkstemp(dir='.', prefix=tempprefix)
    os.close(fd)
    try:
        return util.cachestat(path).cacheable()
    finally:
        os.remove(path)

@check("lsprof", "python lsprof module")
def has_lsprof():
    try:
        import _lsprof
        _lsprof.Profiler # silence unused import warning
        return True
    except ImportError:
        return False

def gethgversion():
    m = matchoutput('hg --version --quiet 2>&1', br'(\d+)\.(\d+)')
    if not m:
        return (0, 0)
    return (int(m.group(1)), int(m.group(2)))

@checkvers("hg", "Mercurial >= %s",
            list([(1.0 * x) / 10 for x in range(9, 99)]))
def has_hg_range(v):
    major, minor = v.split('.')[0:2]
    return gethgversion() >= (int(major), int(minor))

@check("hg08", "Mercurial >= 0.8")
def has_hg08():
    if checks["hg09"][0]():
        return True
    return matchoutput('hg help annotate 2>&1', '--date')

@check("hg07", "Mercurial >= 0.7")
def has_hg07():
    if checks["hg08"][0]():
        return True
    return matchoutput('hg --version --quiet 2>&1', 'Mercurial Distributed SCM')

@check("hg06", "Mercurial >= 0.6")
def has_hg06():
    if checks["hg07"][0]():
        return True
    return matchoutput('hg --version --quiet 2>&1', 'Mercurial version')

@check("gettext", "GNU Gettext (msgfmt)")
def has_gettext():
    return matchoutput('msgfmt --version', br'GNU gettext-tools')

@check("git", "git command line client")
def has_git():
    return matchoutput('git --version 2>&1', br'^git version')

def getgitversion():
    m = matchoutput('git --version 2>&1', br'git version (\d+)\.(\d+)')
    if not m:
        return (0, 0)
    return (int(m.group(1)), int(m.group(2)))

# https://github.com/git-lfs/lfs-test-server
@check("lfs-test-server", "git-lfs test server")
def has_lfsserver():
    exe = 'lfs-test-server'
    if has_windows():
        exe = 'lfs-test-server.exe'
    return any(
        os.access(os.path.join(path, exe), os.X_OK)
        for path in os.environ["PATH"].split(os.pathsep)
    )

@checkvers("git", "git client (with ext::sh support) version >= %s", (1.9,))
def has_git_range(v):
    major, minor = v.split('.')[0:2]
    return getgitversion() >= (int(major), int(minor))

@check("docutils", "Docutils text processing library")
def has_docutils():
    try:
        import docutils.core
        docutils.core.publish_cmdline # silence unused import
        return True
    except ImportError:
        return False

def getsvnversion():
    m = matchoutput('svn --version --quiet 2>&1', br'^(\d+)\.(\d+)')
    if not m:
        return (0, 0)
    return (int(m.group(1)), int(m.group(2)))

@checkvers("svn", "subversion client and admin tools >= %s", (1.3, 1.5))
def has_svn_range(v):
    major, minor = v.split('.')[0:2]
    return getsvnversion() >= (int(major), int(minor))

@check("svn", "subversion client and admin tools")
def has_svn():
    return (matchoutput('svn --version 2>&1', br'^svn, version') and
            matchoutput('svnadmin --version 2>&1', br'^svnadmin, version'))

@check("svn-bindings", "subversion python bindings")
def has_svn_bindings():
    try:
        import svn.core
        version = svn.core.SVN_VER_MAJOR, svn.core.SVN_VER_MINOR
        if version < (1, 4):
            return False
        return True
    except ImportError:
        return False

@check("p4", "Perforce server and client")
def has_p4():
    return (matchoutput('p4 -V', br'Rev\. P4/') and
            matchoutput('p4d -V', br'Rev\. P4D/'))

@check("symlink", "symbolic links")
def has_symlink():
    if getattr(os, "symlink", None) is None:
        return False
    name = tempfile.mktemp(dir='.', prefix=tempprefix)
    try:
        os.symlink(".", name)
        os.unlink(name)
        return True
    except (OSError, AttributeError):
        return False

@check("hardlink", "hardlinks")
def has_hardlink():
    from mercurial import util
    fh, fn = tempfile.mkstemp(dir='.', prefix=tempprefix)
    os.close(fh)
    name = tempfile.mktemp(dir='.', prefix=tempprefix)
    try:
        util.oslink(_bytespath(fn), _bytespath(name))
        os.unlink(name)
        return True
    except OSError:
        return False
    finally:
        os.unlink(fn)

@check("hardlink-whitelisted", "hardlinks on whitelisted filesystems")
def has_hardlink_whitelisted():
    from mercurial import util
    try:
        fstype = util.getfstype(b'.')
    except OSError:
        return False
    return fstype in util._hardlinkfswhitelist

@check("rmcwd", "can remove current working directory")
def has_rmcwd():
    ocwd = os.getcwd()
    temp = tempfile.mkdtemp(dir='.', prefix=tempprefix)
    try:
        os.chdir(temp)
        # On Linux, 'rmdir .' isn't allowed, but the other names are okay.
        # On Solaris and Windows, the cwd can't be removed by any names.
        os.rmdir(os.getcwd())
        return True
    except OSError:
        return False
    finally:
        os.chdir(ocwd)
        # clean up temp dir on platforms where cwd can't be removed
        try:
            os.rmdir(temp)
        except OSError:
            pass

@check("tla", "GNU Arch tla client")
def has_tla():
    return matchoutput('tla --version 2>&1', br'The GNU Arch Revision')

@check("gpg", "gpg client")
def has_gpg():
    return matchoutput('gpg --version 2>&1', br'GnuPG')

@check("gpg2", "gpg client v2")
def has_gpg2():
    return matchoutput('gpg --version 2>&1', br'GnuPG[^0-9]+2\.')

@check("gpg21", "gpg client v2.1+")
def has_gpg21():
    return matchoutput('gpg --version 2>&1', br'GnuPG[^0-9]+2\.(?!0)')

@check("unix-permissions", "unix-style permissions")
def has_unix_permissions():
    d = tempfile.mkdtemp(dir='.', prefix=tempprefix)
    try:
        fname = os.path.join(d, 'foo')
        for umask in (0o77, 0o07, 0o22):
            os.umask(umask)
            f = open(fname, 'w')
            f.close()
            mode = os.stat(fname).st_mode
            os.unlink(fname)
            if mode & 0o777 != ~umask & 0o666:
                return False
        return True
    finally:
        os.rmdir(d)

@check("unix-socket", "AF_UNIX socket family")
def has_unix_socket():
    return getattr(socket, 'AF_UNIX', None) is not None

@check("root", "root permissions")
def has_root():
    return getattr(os, 'geteuid', None) and os.geteuid() == 0

@check("pyflakes", "Pyflakes python linter")
def has_pyflakes():
    return matchoutput("sh -c \"echo 'import re' 2>&1 | pyflakes\"",
                       br"<stdin>:1: 're' imported but unused",
                       True)

@check("pylint", "Pylint python linter")
def has_pylint():
    return matchoutput("pylint --help",
                       br"Usage:  pylint",
                       True)

@check("clang-format", "clang-format C code formatter")
def has_clang_format():
    m = matchoutput('clang-format --version', br'clang-format version (\d)')
    # style changed somewhere between 4.x and 6.x
    return m and int(m.group(1)) >= 6

@check("jshint", "JSHint static code analysis tool")
def has_jshint():
    return matchoutput("jshint --version 2>&1", br"jshint v")

@check("pygments", "Pygments source highlighting library")
def has_pygments():
    try:
        import pygments
        pygments.highlight # silence unused import warning
        return True
    except ImportError:
        return False

@check("outer-repo", "outer repo")
def has_outer_repo():
    # failing for other reasons than 'no repo' imply that there is a repo
    return not matchoutput('hg root 2>&1',
                           br'abort: no repository found', True)

@check("ssl", "ssl module available")
def has_ssl():
    try:
        import ssl
        ssl.CERT_NONE
        return True
    except ImportError:
        return False

@check("sslcontext", "python >= 2.7.9 ssl")
def has_sslcontext():
    try:
        import ssl
        ssl.SSLContext
        return True
    except (ImportError, AttributeError):
        return False

@check("defaultcacerts", "can verify SSL certs by system's CA certs store")
def has_defaultcacerts():
    from mercurial import sslutil, ui as uimod
    ui = uimod.ui.load()
    return sslutil._defaultcacerts(ui) or sslutil._canloaddefaultcerts

@check("defaultcacertsloaded", "detected presence of loaded system CA certs")
def has_defaultcacertsloaded():
    import ssl
    from mercurial import sslutil, ui as uimod

    if not has_defaultcacerts():
        return False
    if not has_sslcontext():
        return False

    ui = uimod.ui.load()
    cafile = sslutil._defaultcacerts(ui)
    ctx = ssl.create_default_context()
    if cafile:
        ctx.load_verify_locations(cafile=cafile)
    else:
        ctx.load_default_certs()

    return len(ctx.get_ca_certs()) > 0

@check("tls1.2", "TLS 1.2 protocol support")
def has_tls1_2():
    from mercurial import sslutil
    return b'tls1.2' in sslutil.supportedprotocols

@check("windows", "Windows")
def has_windows():
    return os.name == 'nt'

@check("system-sh", "system() uses sh")
def has_system_sh():
    return os.name != 'nt'

@check("serve", "platform and python can manage 'hg serve -d'")
def has_serve():
    return True

@check("test-repo", "running tests from repository")
def has_test_repo():
    t = os.environ["TESTDIR"]
    return os.path.isdir(os.path.join(t, "..", ".hg"))

@check("tic", "terminfo compiler and curses module")
def has_tic():
    try:
        import curses
        curses.COLOR_BLUE
        return matchoutput('test -x "`which tic`"', br'')
    except ImportError:
        return False

@check("msys", "Windows with MSYS")
def has_msys():
    return os.getenv('MSYSTEM')

@check("aix", "AIX")
def has_aix():
    return sys.platform.startswith("aix")

@check("osx", "OS X")
def has_osx():
    return sys.platform == 'darwin'

@check("osxpackaging", "OS X packaging tools")
def has_osxpackaging():
    try:
        return (matchoutput('pkgbuild', br'Usage: pkgbuild ', ignorestatus=1)
                and matchoutput(
                    'productbuild', br'Usage: productbuild ',
                    ignorestatus=1)
                and matchoutput('lsbom', br'Usage: lsbom', ignorestatus=1)
                and matchoutput(
                    'xar --help', br'Usage: xar', ignorestatus=1))
    except ImportError:
        return False

@check('linuxormacos', 'Linux or MacOS')
def has_linuxormacos():
    # This isn't a perfect test for MacOS. But it is sufficient for our needs.
    return sys.platform.startswith(('linux', 'darwin'))

@check("docker", "docker support")
def has_docker():
    pat = br'A self-sufficient runtime for'
    if matchoutput('docker --help', pat):
        if 'linux' not in sys.platform:
            # TODO: in theory we should be able to test docker-based
            # package creation on non-linux using boot2docker, but in
            # practice that requires extra coordination to make sure
            # $TESTTEMP is going to be visible at the same path to the
            # boot2docker VM. If we figure out how to verify that, we
            # can use the following instead of just saying False:
            # return 'DOCKER_HOST' in os.environ
            return False

        return True
    return False

@check("debhelper", "debian packaging tools")
def has_debhelper():
    # Some versions of dpkg say `dpkg', some say 'dpkg' (` vs ' on the first
    # quote), so just accept anything in that spot.
    dpkg = matchoutput('dpkg --version',
                       br"Debian .dpkg' package management program")
    dh = matchoutput('dh --help',
                     br'dh is a part of debhelper.', ignorestatus=True)
    dh_py2 = matchoutput('dh_python2 --help',
                         br'other supported Python versions')
    # debuild comes from the 'devscripts' package, though you might want
    # the 'build-debs' package instead, which has a dependency on devscripts.
    debuild = matchoutput('debuild --help',
                          br'to run debian/rules with given parameter')
    return dpkg and dh and dh_py2 and debuild

@check("debdeps",
       "debian build dependencies (run dpkg-checkbuilddeps in contrib/)")
def has_debdeps():
    # just check exit status (ignoring output)
    path = '%s/../contrib/packaging/debian/control' % os.environ['TESTDIR']
    return matchoutput('dpkg-checkbuilddeps %s' % path, br'')

@check("demandimport", "demandimport enabled")
def has_demandimport():
    # chg disables demandimport intentionally for performance wins.
    return ((not has_chg()) and os.environ.get('HGDEMANDIMPORT') != 'disable')

@checkvers("py", "Python >= %s", (2.7, 3.5, 3.6, 3.7, 3.8, 3.9))
def has_python_range(v):
    major, minor = v.split('.')[0:2]
    py_major, py_minor = sys.version_info.major, sys.version_info.minor

    return (py_major, py_minor) >= (int(major), int(minor))

@check("py3", "running with Python 3.x")
def has_py3():
    return 3 == sys.version_info[0]

@check("py3exe", "a Python 3.x interpreter is available")
def has_python3exe():
    return matchoutput('python3 -V', br'^Python 3.(5|6|7|8|9)')

@check("pure", "running with pure Python code")
def has_pure():
    return any([
        os.environ.get("HGMODULEPOLICY") == "py",
        os.environ.get("HGTEST_RUN_TESTS_PURE") == "--pure",
    ])

@check("slow", "allow slow tests (use --allow-slow-tests)")
def has_slow():
    return os.environ.get('HGTEST_SLOW') == 'slow'

@check("hypothesis", "Hypothesis automated test generation")
def has_hypothesis():
    try:
        import hypothesis
        hypothesis.given
        return True
    except ImportError:
        return False

@check("unziplinks", "unzip(1) understands and extracts symlinks")
def unzip_understands_symlinks():
    return matchoutput('unzip --help', br'Info-ZIP')

@check("zstd", "zstd Python module available")
def has_zstd():
    try:
        import mercurial.zstd
        mercurial.zstd.__version__
        return True
    except ImportError:
        return False

@check("devfull", "/dev/full special file")
def has_dev_full():
    return os.path.exists('/dev/full')

@check("virtualenv", "Python virtualenv support")
def has_virtualenv():
    try:
        import virtualenv
        virtualenv.ACTIVATE_SH
        return True
    except ImportError:
        return False

@check("fsmonitor", "running tests with fsmonitor")
def has_fsmonitor():
    return 'HGFSMONITOR_TESTS' in os.environ

@check("fuzzywuzzy", "Fuzzy string matching library")
def has_fuzzywuzzy():
    try:
        import fuzzywuzzy
        fuzzywuzzy.__version__
        return True
    except ImportError:
        return False

@check("clang-libfuzzer", "clang new enough to include libfuzzer")
def has_clang_libfuzzer():
    mat = matchoutput('clang --version', br'clang version (\d)')
    if mat:
        # libfuzzer is new in clang 6
        return int(mat.group(1)) > 5
    return False

@check("clang-6.0", "clang 6.0 with version suffix (libfuzzer included)")
def has_clang60():
    return matchoutput('clang-6.0 --version', br'clang version 6\.')

@check("xdiff", "xdiff algorithm")
def has_xdiff():
    try:
        from mercurial import policy
        bdiff = policy.importmod('bdiff')
        return bdiff.xdiffblocks(b'', b'') == [(0, 0, 0, 0)]
    except (ImportError, AttributeError):
        return False

@check('extraextensions', 'whether tests are running with extra extensions')
def has_extraextensions():
    return 'HGTESTEXTRAEXTENSIONS' in os.environ

def getrepofeatures():
    """Obtain set of repository features in use.

    HGREPOFEATURES can be used to define or remove features. It contains
    a space-delimited list of feature strings. Strings beginning with ``-``
    mean to remove.
    """
    # Default list provided by core.
    features = {
        'bundlerepo',
        'revlogstore',
        'fncache',
    }

    # Features that imply other features.
    implies = {
        'simplestore': ['-revlogstore', '-bundlerepo', '-fncache'],
    }

    for override in os.environ.get('HGREPOFEATURES', '').split(' '):
        if not override:
            continue

        if override.startswith('-'):
            if override[1:] in features:
                features.remove(override[1:])
        else:
            features.add(override)

            for imply in implies.get(override, []):
                if imply.startswith('-'):
                    if imply[1:] in features:
                        features.remove(imply[1:])
                else:
                    features.add(imply)

    return features

@check('reporevlogstore', 'repository using the default revlog store')
def has_reporevlogstore():
    return 'revlogstore' in getrepofeatures()

@check('reposimplestore', 'repository using simple storage extension')
def has_reposimplestore():
    return 'simplestore' in getrepofeatures()

@check('repobundlerepo', 'whether we can open bundle files as repos')
def has_repobundlerepo():
    return 'bundlerepo' in getrepofeatures()

@check('repofncache', 'repository has an fncache')
def has_repofncache():
    return 'fncache' in getrepofeatures()

@check('sqlite', 'sqlite3 module is available')
def has_sqlite():
    try:
        import sqlite3
        version = sqlite3.sqlite_version_info
    except ImportError:
        return False

    if version < (3, 8, 3):
        # WITH clause not supported
        return False

    return matchoutput('sqlite3 -version', br'^3\.\d+')

@check('vcr', 'vcr http mocking library')
def has_vcr():
    try:
        import vcr
        vcr.VCR
        return True
    except (ImportError, AttributeError):
        pass
    return False

@check('emacs', 'GNU Emacs')
def has_emacs():
    # Our emacs lisp uses `with-eval-after-load` which is new in emacs
    # 24.4, so we allow emacs 24.4, 24.5, and 25+ (24.5 was the last
    # 24 release)
    return matchoutput('emacs --version', b'GNU Emacs 2(4.4|4.5|5|6|7|8|9)')
