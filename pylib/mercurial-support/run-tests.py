#!/usr/bin/env python
#
# run-tests.py - Run a set of tests on Mercurial
#
# Copyright 2006 Matt Mackall <mpm@selenic.com>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

# Modifying this script is tricky because it has many modes:
#   - serial (default) vs parallel (-jN, N > 1)
#   - no coverage (default) vs coverage (-c, -C, -s)
#   - temp install (default) vs specific hg script (--with-hg, --local)
#   - tests are a mix of shell scripts and Python scripts
#
# If you change this script, it is recommended that you ensure you
# haven't broken it by running it in various modes with a representative
# sample of test scripts.  For example:
#
#  1) serial, no coverage, temp install:
#      ./run-tests.py test-s*
#  2) serial, no coverage, local hg:
#      ./run-tests.py --local test-s*
#  3) serial, coverage, temp install:
#      ./run-tests.py -c test-s*
#  4) serial, coverage, local hg:
#      ./run-tests.py -c --local test-s*      # unsupported
#  5) parallel, no coverage, temp install:
#      ./run-tests.py -j2 test-s*
#  6) parallel, no coverage, local hg:
#      ./run-tests.py -j2 --local test-s*
#  7) parallel, coverage, temp install:
#      ./run-tests.py -j2 -c test-s*          # currently broken
#  8) parallel, coverage, local install:
#      ./run-tests.py -j2 -c --local test-s*  # unsupported (and broken)
#  9) parallel, custom tmp dir:
#      ./run-tests.py -j2 --tmpdir /tmp/myhgtests
#  10) parallel, pure, tests that call run-tests:
#      ./run-tests.py --pure `grep -l run-tests.py *.t`
#
# (You could use any subset of the tests: test-s* happens to match
# enough that it's worth doing parallel runs, few enough that it
# completes fairly quickly, includes both shell and Python scripts, and
# includes some scripts that run daemon processes.)

from __future__ import absolute_import, print_function

import argparse
import collections
import difflib
import distutils.version as version
import errno
import json
import multiprocessing
import os
import random
import re
import shutil
import signal
import socket
import subprocess
import sys
import sysconfig
import tempfile
import threading
import time
import unittest
import uuid
import xml.dom.minidom as minidom

try:
    import Queue as queue
except ImportError:
    import queue

try:
    import shlex

    shellquote = shlex.quote
except (ImportError, AttributeError):
    import pipes

    shellquote = pipes.quote

processlock = threading.Lock()

pygmentspresent = False
# ANSI color is unsupported prior to Windows 10
if os.name != 'nt':
    try:  # is pygments installed
        import pygments
        import pygments.lexers as lexers
        import pygments.lexer as lexer
        import pygments.formatters as formatters
        import pygments.token as token
        import pygments.style as style

        pygmentspresent = True
        difflexer = lexers.DiffLexer()
        terminal256formatter = formatters.Terminal256Formatter()
    except ImportError:
        pass

if pygmentspresent:

    class TestRunnerStyle(style.Style):
        default_style = ""
        skipped = token.string_to_tokentype("Token.Generic.Skipped")
        failed = token.string_to_tokentype("Token.Generic.Failed")
        skippedname = token.string_to_tokentype("Token.Generic.SName")
        failedname = token.string_to_tokentype("Token.Generic.FName")
        styles = {
            skipped: '#e5e5e5',
            skippedname: '#00ffff',
            failed: '#7f0000',
            failedname: '#ff0000',
        }

    class TestRunnerLexer(lexer.RegexLexer):
        testpattern = r'[\w-]+\.(t|py)(#[a-zA-Z0-9_\-\.]+)?'
        tokens = {
            'root': [
                (r'^Skipped', token.Generic.Skipped, 'skipped'),
                (r'^Failed ', token.Generic.Failed, 'failed'),
                (r'^ERROR: ', token.Generic.Failed, 'failed'),
            ],
            'skipped': [
                (testpattern, token.Generic.SName),
                (r':.*', token.Generic.Skipped),
            ],
            'failed': [
                (testpattern, token.Generic.FName),
                (r'(:| ).*', token.Generic.Failed),
            ],
        }

    runnerformatter = formatters.Terminal256Formatter(style=TestRunnerStyle)
    runnerlexer = TestRunnerLexer()

origenviron = os.environ.copy()

if sys.version_info > (3, 5, 0):
    PYTHON3 = True
    xrange = range  # we use xrange in one place, and we'd rather not use range

    def _bytespath(p):
        if p is None:
            return p
        return p.encode('utf-8')

    def _strpath(p):
        if p is None:
            return p
        return p.decode('utf-8')

    osenvironb = getattr(os, 'environb', None)
    if osenvironb is None:
        # Windows lacks os.environb, for instance.  A proxy over the real thing
        # instead of a copy allows the environment to be updated via bytes on
        # all platforms.
        class environbytes(object):
            def __init__(self, strenv):
                self.__len__ = strenv.__len__
                self.clear = strenv.clear
                self._strenv = strenv

            def __getitem__(self, k):
                v = self._strenv.__getitem__(_strpath(k))
                return _bytespath(v)

            def __setitem__(self, k, v):
                self._strenv.__setitem__(_strpath(k), _strpath(v))

            def __delitem__(self, k):
                self._strenv.__delitem__(_strpath(k))

            def __contains__(self, k):
                return self._strenv.__contains__(_strpath(k))

            def __iter__(self):
                return iter([_bytespath(k) for k in iter(self._strenv)])

            def get(self, k, default=None):
                v = self._strenv.get(_strpath(k), _strpath(default))
                return _bytespath(v)

            def pop(self, k, default=None):
                v = self._strenv.pop(_strpath(k), _strpath(default))
                return _bytespath(v)

        osenvironb = environbytes(os.environ)

    getcwdb = getattr(os, 'getcwdb')
    if not getcwdb or os.name == 'nt':
        getcwdb = lambda: _bytespath(os.getcwd())

elif sys.version_info >= (3, 0, 0):
    print(
        '%s is only supported on Python 3.5+ and 2.7, not %s'
        % (sys.argv[0], '.'.join(str(v) for v in sys.version_info[:3]))
    )
    sys.exit(70)  # EX_SOFTWARE from `man 3 sysexit`
else:
    PYTHON3 = False

    # In python 2.x, path operations are generally done using
    # bytestrings by default, so we don't have to do any extra
    # fiddling there. We define the wrapper functions anyway just to
    # help keep code consistent between platforms.
    def _bytespath(p):
        return p

    _strpath = _bytespath
    osenvironb = os.environ
    getcwdb = os.getcwd

# For Windows support
wifexited = getattr(os, "WIFEXITED", lambda x: False)

# TRACKING MOZ
# Add a few constant variables
HERE = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))

# Whether to use IPv6
def checksocketfamily(name, port=20058):
    """return true if we can listen on localhost using family=name

    name should be either 'AF_INET', or 'AF_INET6'.
    port being used is okay - EADDRINUSE is considered as successful.
    """
    family = getattr(socket, name, None)
    if family is None:
        return False
    try:
        s = socket.socket(family, socket.SOCK_STREAM)
        s.bind(('localhost', port))
        s.close()
        return True
    except socket.error as exc:
        if exc.errno == errno.EADDRINUSE:
            return True
        elif exc.errno in (errno.EADDRNOTAVAIL, errno.EPROTONOSUPPORT):
            return False
        else:
            raise
    else:
        return False


# useipv6 will be set by parseargs
useipv6 = None


def checkportisavailable(port):
    """return true if a port seems free to bind on localhost"""
    if useipv6:
        family = socket.AF_INET6
    else:
        family = socket.AF_INET
    try:
        s = socket.socket(family, socket.SOCK_STREAM)
        s.bind(('localhost', port))
        s.close()
        return True
    except socket.error as exc:
        if exc.errno not in (
            errno.EADDRINUSE,
            errno.EADDRNOTAVAIL,
            errno.EPROTONOSUPPORT,
        ):
            raise
    return False


closefds = os.name == 'posix'


def Popen4(cmd, wd, timeout, env=None):
    processlock.acquire()
    p = subprocess.Popen(
        _strpath(cmd),
        shell=True,
        bufsize=-1,
        cwd=_strpath(wd),
        env=env,
        close_fds=closefds,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    processlock.release()

    p.fromchild = p.stdout
    p.tochild = p.stdin
    p.childerr = p.stderr

    p.timeout = False
    if timeout:

        def t():
            start = time.time()
            while time.time() - start < timeout and p.returncode is None:
                time.sleep(0.1)
            p.timeout = True
            if p.returncode is None:
                terminate(p)

        threading.Thread(target=t).start()

    return p


if sys.executable:
    sysexecutable = sys.executable
elif os.environ.get('PYTHONEXECUTABLE'):
    sysexecutable = os.environ['PYTHONEXECUTABLE']
elif os.environ.get('PYTHON'):
    sysexecutable = os.environ['PYTHON']
else:
    raise AssertionError('Could not find Python interpreter')

PYTHON = _bytespath(sysexecutable.replace('\\', '/'))
IMPL_PATH = b'PYTHONPATH'
if 'java' in sys.platform:
    IMPL_PATH = b'JYTHONPATH'

defaults = {
    'jobs': ('HGTEST_JOBS', multiprocessing.cpu_count()),
    'timeout': ('HGTEST_TIMEOUT', 180),
    'slowtimeout': ('HGTEST_SLOWTIMEOUT', 1500),
    'port': ('HGTEST_PORT', 20059),
    'shell': ('HGTEST_SHELL', 'sh'),
}


def canonpath(path):
    return os.path.realpath(os.path.expanduser(path))


def parselistfiles(files, listtype, warn=True):
    entries = dict()
    for filename in files:
        try:
            path = os.path.expanduser(os.path.expandvars(filename))
            f = open(path, "rb")
        except IOError as err:
            if err.errno != errno.ENOENT:
                raise
            if warn:
                print("warning: no such %s file: %s" % (listtype, filename))
            continue

        for line in f.readlines():
            line = line.split(b'#', 1)[0].strip()
            if line:
                entries[line] = filename

        f.close()
    return entries


def parsettestcases(path):
    """read a .t test file, return a set of test case names

    If path does not exist, return an empty set.
    """
    cases = []
    try:
        with open(path, 'rb') as f:
            for l in f:
                if l.startswith(b'#testcases '):
                    cases.append(sorted(l[11:].split()))
    except IOError as ex:
        if ex.errno != errno.ENOENT:
            raise
    return cases


def getparser():
    """Obtain the OptionParser used by the CLI."""
    parser = argparse.ArgumentParser(usage='%(prog)s [options] [tests]')

    selection = parser.add_argument_group('Test Selection')
    selection.add_argument(
        '--allow-slow-tests',
        action='store_true',
        help='allow extremely slow tests',
    )
    selection.add_argument(
        "--blacklist",
        action="append",
        help="skip tests listed in the specified blacklist file",
    )
    selection.add_argument(
        "--changed",
        help="run tests that are changed in parent rev or working directory",
    )
    selection.add_argument(
        "-k", "--keywords", help="run tests matching keywords"
    )
    selection.add_argument(
        "-r", "--retest", action="store_true", help="retest failed tests"
    )
    selection.add_argument(
        "--test-list",
        action="append",
        help="read tests to run from the specified file",
    )
    selection.add_argument(
        "--whitelist",
        action="append",
        help="always run tests listed in the specified whitelist file",
    )
    selection.add_argument(
        'tests', metavar='TESTS', nargs='*', help='Tests to run'
    )

    harness = parser.add_argument_group('Test Harness Behavior')
    harness.add_argument(
        '--bisect-repo',
        metavar='bisect_repo',
        help=(
            "Path of a repo to bisect. Use together with --known-good-rev"
        ),
    )
    harness.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="debug mode: write output of test scripts to console"
        " rather than capturing and diffing it (disables timeout)",
    )
    harness.add_argument(
        "-f",
        "--first",
        action="store_true",
        help="exit on the first test failure",
    )
    harness.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="prompt to accept changed output",
    )
    harness.add_argument(
        "-j",
        "--jobs",
        type=int,
        help="number of jobs to run in parallel"
        " (default: $%s or %d)" % defaults['jobs'],
    )
    harness.add_argument(
        "--keep-tmpdir",
        action="store_true",
        help="keep temporary directory after running tests",
    )
    harness.add_argument(
        '--known-good-rev',
        metavar="known_good_rev",
        help=(
            "Automatically bisect any failures using this "
            "revision as a known-good revision."
        ),
    )
    harness.add_argument(
        "--list-tests",
        action="store_true",
        help="list tests instead of running them",
    )
    harness.add_argument(
        "--loop", action="store_true", help="loop tests repeatedly"
    )
    harness.add_argument(
        '--random', action="store_true", help='run tests in random order'
    )
    harness.add_argument(
        '--order-by-runtime',
        action="store_true",
        help='run slowest tests first, according to .testtimes',
    )
    harness.add_argument(
        "-p",
        "--port",
        type=int,
        help="port on which servers should listen"
        " (default: $%s or %d)" % defaults['port'],
    )
    harness.add_argument(
        '--profile-runner',
        action='store_true',
        help='run statprof on run-tests',
    )
    harness.add_argument(
        "-R", "--restart", action="store_true", help="restart at last error"
    )
    harness.add_argument(
        "--runs-per-test",
        type=int,
        dest="runs_per_test",
        help="run each test N times (default=1)",
        default=1,
    )
    harness.add_argument(
        "--shell", help="shell to use (default: $%s or %s)" % defaults['shell']
    )
    harness.add_argument(
        '--showchannels', action='store_true', help='show scheduling channels'
    )
    harness.add_argument(
        "--slowtimeout",
        type=int,
        help="kill errant slow tests after SLOWTIMEOUT seconds"
        " (default: $%s or %d)" % defaults['slowtimeout'],
    )
    harness.add_argument(
        "-t",
        "--timeout",
        type=int,
        help="kill errant tests after TIMEOUT seconds"
        " (default: $%s or %d)" % defaults['timeout'],
    )
    harness.add_argument(
        "--tmpdir",
        help="run tests in the given temporary directory"
        " (implies --keep-tmpdir)",
    )
    harness.add_argument(
        "-v", "--verbose", action="store_true", help="output verbose messages"
    )

    hgconf = parser.add_argument_group('Mercurial Configuration')
    hgconf.add_argument(
        "--chg",
        action="store_true",
        help="install and use chg wrapper in place of hg",
    )
    hgconf.add_argument("--compiler", help="compiler to build with")
    hgconf.add_argument(
        '--extra-config-opt',
        action="append",
        default=[],
        help='set the given config opt in the test hgrc',
    )
    hgconf.add_argument(
        "-l",
        "--local",
        action="store_true",
        help="shortcut for --with-hg=<testdir>/../hg, "
        "and --with-chg=<testdir>/../contrib/chg/chg if --chg is set",
    )
    hgconf.add_argument(
        "--ipv6",
        action="store_true",
        help="prefer IPv6 to IPv4 for network related tests",
    )
    hgconf.add_argument(
        "--pure",
        action="store_true",
        help="use pure Python code instead of C extensions",
    )
    hgconf.add_argument(
        "-3",
        "--py3-warnings",
        action="store_true",
        help="enable Py3k warnings on Python 2.7+",
    )
    hgconf.add_argument(
        "--with-chg",
        metavar="CHG",
        help="use specified chg wrapper in place of hg",
    )
    hgconf.add_argument(
        "--with-hg",
        metavar="HG",
        help="test using specified hg script rather than a "
        "temporary installation",
    )

    reporting = parser.add_argument_group('Results Reporting')
    reporting.add_argument(
        "-C",
        "--annotate",
        action="store_true",
        help="output files annotated with coverage",
    )
    reporting.add_argument(
        "--color",
        choices=["always", "auto", "never"],
        default=os.environ.get('HGRUNTESTSCOLOR', 'auto'),
        help="colorisation: always|auto|never (default: auto)",
    )
    reporting.add_argument(
        "-c",
        "--cover",
        action="store_true",
        help="print a test coverage report",
    )
    reporting.add_argument(
        '--exceptions',
        action='store_true',
        help='log all exceptions and generate an exception report',
    )
    reporting.add_argument(
        "-H",
        "--htmlcov",
        action="store_true",
        help="create an HTML report of the coverage of the files",
    )
    reporting.add_argument(
        "--json",
        action="store_true",
        help="store test result data in 'report.json' file",
    )
    reporting.add_argument(
        "--outputdir",
        help="directory to write error logs to (default=test directory)",
    )
    reporting.add_argument(
        "-n", "--nodiff", action="store_true", help="skip showing test changes"
    )
    reporting.add_argument(
        "-S",
        "--noskips",
        action="store_true",
        help="don't report skip tests verbosely",
    )
    reporting.add_argument(
        "--time", action="store_true", help="time how long each test takes"
    )
    reporting.add_argument("--view", help="external diff viewer")
    reporting.add_argument(
        "--xunit", help="record xunit results at specified path"
    )

    for option, (envvar, default) in defaults.items():
        defaults[option] = type(default)(os.environ.get(envvar, default))
    parser.set_defaults(**defaults)

    return parser


def parseargs(args, parser):
    """Parse arguments with our OptionParser and validate results."""
    options = parser.parse_args(args)

    # jython is always pure
    if 'java' in sys.platform or '__pypy__' in sys.modules:
        options.pure = True

    if options.local:
        if options.with_hg or options.with_chg:
            parser.error('--local cannot be used with --with-hg or --with-chg')
        testdir = os.path.dirname(_bytespath(canonpath(sys.argv[0])))
        reporootdir = os.path.dirname(testdir)
        pathandattrs = [(b'hg', 'with_hg')]
        if options.chg:
            pathandattrs.append((b'contrib/chg/chg', 'with_chg'))
        for relpath, attr in pathandattrs:
            binpath = os.path.join(reporootdir, relpath)
            if os.name != 'nt' and not os.access(binpath, os.X_OK):
                parser.error(
                    '--local specified, but %r not found or '
                    'not executable' % binpath
                )
            setattr(options, attr, _strpath(binpath))

    if options.with_hg:
        options.with_hg = canonpath(_bytespath(options.with_hg))
        if not (
            os.path.isfile(options.with_hg)
            and os.access(options.with_hg, os.X_OK)
        ):
            parser.error('--with-hg must specify an executable hg script')
        if os.path.basename(options.with_hg) not in [b'hg', b'hg.exe']:
            sys.stderr.write('warning: --with-hg should specify an hg script\n')
            sys.stderr.flush()

    if (options.chg or options.with_chg) and os.name == 'nt':
        parser.error('chg does not work on %s' % os.name)
    if options.with_chg:
        options.chg = False  # no installation to temporary location
        options.with_chg = canonpath(_bytespath(options.with_chg))
        if not (
            os.path.isfile(options.with_chg)
            and os.access(options.with_chg, os.X_OK)
        ):
            parser.error('--with-chg must specify a chg executable')
    if options.chg and options.with_hg:
        # chg shares installation location with hg
        parser.error(
            '--chg does not work when --with-hg is specified '
            '(use --with-chg instead)'
        )

    if options.color == 'always' and not pygmentspresent:
        sys.stderr.write(
            'warning: --color=always ignored because '
            'pygments is not installed\n'
        )

    if options.bisect_repo and not options.known_good_rev:
        parser.error("--bisect-repo cannot be used without --known-good-rev")

    global useipv6
    if options.ipv6:
        useipv6 = checksocketfamily('AF_INET6')
    else:
        # only use IPv6 if IPv4 is unavailable and IPv6 is available
        useipv6 = (not checksocketfamily('AF_INET')) and checksocketfamily(
            'AF_INET6'
        )

    options.anycoverage = options.cover or options.annotate or options.htmlcov
    if options.anycoverage:
        try:
            import coverage

            covver = version.StrictVersion(coverage.__version__).version
            if covver < (3, 3):
                parser.error('coverage options require coverage 3.3 or later')
        except ImportError:
            parser.error('coverage options now require the coverage package')

    if options.anycoverage and options.local:
        # this needs some path mangling somewhere, I guess
        parser.error(
            "sorry, coverage options do not work when --local is specified"
        )

    if options.anycoverage and options.with_hg:
        parser.error(
            "sorry, coverage options do not work when --with-hg is specified"
        )

    global verbose
    if options.verbose:
        verbose = ''

    if options.tmpdir:
        options.tmpdir = canonpath(options.tmpdir)

    if options.jobs < 1:
        parser.error('--jobs must be positive')
    if options.interactive and options.debug:
        parser.error("-i/--interactive and -d/--debug are incompatible")
    if options.debug:
        if options.timeout != defaults['timeout']:
            sys.stderr.write('warning: --timeout option ignored with --debug\n')
        if options.slowtimeout != defaults['slowtimeout']:
            sys.stderr.write(
                'warning: --slowtimeout option ignored with --debug\n'
            )
        options.timeout = 0
        options.slowtimeout = 0
    if options.py3_warnings:
        if PYTHON3:
            parser.error('--py3-warnings can only be used on Python 2.7')

    if options.blacklist:
        options.blacklist = parselistfiles(options.blacklist, 'blacklist')
    if options.whitelist:
        options.whitelisted = parselistfiles(options.whitelist, 'whitelist')
    else:
        options.whitelisted = {}

    if options.showchannels:
        options.nodiff = True

    return options


def rename(src, dst):
    """Like os.rename(), trade atomicity and opened files friendliness
    for existing destination support.
    """
    shutil.copy(src, dst)
    os.remove(src)


def makecleanable(path):
    """Try to fix directory permission recursively so that the entire tree
    can be deleted"""
    for dirpath, dirnames, _filenames in os.walk(path, topdown=True):
        for d in dirnames:
            p = os.path.join(dirpath, d)
            try:
                os.chmod(p, os.stat(p).st_mode & 0o777 | 0o700)  # chmod u+rwx
            except OSError:
                pass


_unified_diff = difflib.unified_diff
if PYTHON3:
    import functools

    _unified_diff = functools.partial(difflib.diff_bytes, difflib.unified_diff)


def getdiff(expected, output, ref, err):
    servefail = False
    lines = []
    for line in _unified_diff(expected, output, ref, err):
        if line.startswith(b'+++') or line.startswith(b'---'):
            line = line.replace(b'\\', b'/')
            if line.endswith(b' \n'):
                line = line[:-2] + b'\n'
        lines.append(line)
        if not servefail and line.startswith(
            b'+  abort: child process failed to start'
        ):
            servefail = True

    return servefail, lines


verbose = False


def vlog(*msg):
    """Log only when in verbose mode."""
    if verbose is False:
        return

    return log(*msg)


# Bytes that break XML even in a CDATA block: control characters 0-31
# sans \t, \n and \r
CDATA_EVIL = re.compile(br"[\000-\010\013\014\016-\037]")

# Match feature conditionalized output lines in the form, capturing the feature
# list in group 2, and the preceeding line output in group 1:
#
#   output..output (feature !)\n
optline = re.compile(br'(.*) \((.+?) !\)\n$')


def cdatasafe(data):
    """Make a string safe to include in a CDATA block.

    Certain control characters are illegal in a CDATA block, and
    there's no way to include a ]]> in a CDATA either. This function
    replaces illegal bytes with ? and adds a space between the ]] so
    that it won't break the CDATA block.
    """
    return CDATA_EVIL.sub(b'?', data).replace(b']]>', b'] ]>')


def log(*msg):
    """Log something to stdout.

    Arguments are strings to print.
    """
    with iolock:
        if verbose:
            print(verbose, end=' ')
        for m in msg:
            print(m, end=' ')
        print()
        sys.stdout.flush()


def highlightdiff(line, color):
    if not color:
        return line
    assert pygmentspresent
    return pygments.highlight(
        line.decode('latin1'), difflexer, terminal256formatter
    ).encode('latin1')


def highlightmsg(msg, color):
    if not color:
        return msg
    assert pygmentspresent
    return pygments.highlight(msg, runnerlexer, runnerformatter)


def terminate(proc):
    """Terminate subprocess"""
    vlog('# Terminating process %d' % proc.pid)
    try:
        proc.terminate()
    except OSError:
        pass


def killdaemons(pidfile):
    import killdaemons as killmod

    return killmod.killdaemons(pidfile, tryhard=False, remove=True, logfn=vlog)


class Test(unittest.TestCase):
    """Encapsulates a single, runnable test.

    While this class conforms to the unittest.TestCase API, it differs in that
    instances need to be instantiated manually. (Typically, unittest.TestCase
    classes are instantiated automatically by scanning modules.)
    """

    # Status code reserved for skipped tests (used by hghave).
    SKIPPED_STATUS = 80

    def __init__(
        self,
        path,
        outputdir,
        tmpdir,
        keeptmpdir=False,
        debug=False,
        first=False,
        timeout=None,
        startport=None,
        extraconfigopts=None,
        py3warnings=False,
        shell=None,
        hgcommand=None,
        slowtimeout=None,
        usechg=False,
        useipv6=False,
    ):
        """Create a test from parameters.

        path is the full path to the file defining the test.

        tmpdir is the main temporary directory to use for this test.

        keeptmpdir determines whether to keep the test's temporary directory
        after execution. It defaults to removal (False).

        debug mode will make the test execute verbosely, with unfiltered
        output.

        timeout controls the maximum run time of the test. It is ignored when
        debug is True. See slowtimeout for tests with #require slow.

        slowtimeout overrides timeout if the test has #require slow.

        startport controls the starting port number to use for this test. Each
        test will reserve 3 port numbers for execution. It is the caller's
        responsibility to allocate a non-overlapping port range to Test
        instances.

        extraconfigopts is an iterable of extra hgrc config options. Values
        must have the form "key=value" (something understood by hgrc). Values
        of the form "foo.key=value" will result in "[foo] key=value".

        py3warnings enables Py3k warnings.

        shell is the shell to execute tests in.
        """
        if timeout is None:
            timeout = defaults['timeout']
        if startport is None:
            startport = defaults['port']
        if slowtimeout is None:
            slowtimeout = defaults['slowtimeout']
        self.path = path
        self.bname = os.path.basename(path)
        self.name = _strpath(self.bname)
        self._testdir = os.path.dirname(path)
        self._outputdir = outputdir
        self._tmpname = os.path.basename(path)
        self.errpath = os.path.join(self._outputdir, b'%s.err' % self.bname)

        self._threadtmp = tmpdir
        self._keeptmpdir = keeptmpdir
        self._debug = debug
        self._first = first
        self._timeout = timeout
        self._slowtimeout = slowtimeout
        self._startport = startport
        self._extraconfigopts = extraconfigopts or []
        self._py3warnings = py3warnings
        self._shell = _bytespath(shell)
        self._hgcommand = hgcommand or b'hg'
        self._usechg = usechg
        self._useipv6 = useipv6

        self._aborted = False
        self._daemonpids = []
        self._finished = None
        self._ret = None
        self._out = None
        self._skipped = None
        self._testtmp = None
        self._chgsockdir = None

        self._refout = self.readrefout()

    def readrefout(self):
        """read reference output"""
        # If we're not in --debug mode and reference output file exists,
        # check test output against it.
        if self._debug:
            return None  # to match "out is None"
        elif os.path.exists(self.refpath):
            with open(self.refpath, 'rb') as f:
                return f.read().splitlines(True)
        else:
            return []

    # needed to get base class __repr__ running
    @property
    def _testMethodName(self):
        return self.name

    def __str__(self):
        return self.name

    def shortDescription(self):
        return self.name

    def setUp(self):
        """Tasks to perform before run()."""
        self._finished = False
        self._ret = None
        self._out = None
        self._skipped = None

        try:
            os.mkdir(self._threadtmp)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

        name = self._tmpname
        self._testtmp = os.path.join(self._threadtmp, name)
        os.mkdir(self._testtmp)

        # Remove any previous output files.
        if os.path.exists(self.errpath):
            try:
                os.remove(self.errpath)
            except OSError as e:
                # We might have raced another test to clean up a .err
                # file, so ignore ENOENT when removing a previous .err
                # file.
                if e.errno != errno.ENOENT:
                    raise

        if self._usechg:
            self._chgsockdir = os.path.join(
                self._threadtmp, b'%s.chgsock' % name
            )
            os.mkdir(self._chgsockdir)

    def run(self, result):
        """Run this test and report results against a TestResult instance."""
        # This function is extremely similar to unittest.TestCase.run(). Once
        # we require Python 2.7 (or at least its version of unittest), this
        # function can largely go away.
        self._result = result
        result.startTest(self)
        try:
            try:
                self.setUp()
            except (KeyboardInterrupt, SystemExit):
                self._aborted = True
                raise
            except Exception:
                result.addError(self, sys.exc_info())
                return

            success = False
            try:
                self.runTest()
            except KeyboardInterrupt:
                self._aborted = True
                raise
            except unittest.SkipTest as e:
                result.addSkip(self, str(e))
                # The base class will have already counted this as a
                # test we "ran", but we want to exclude skipped tests
                # from those we count towards those run.
                result.testsRun -= 1
            except self.failureException as e:
                # This differs from unittest in that we don't capture
                # the stack trace. This is for historical reasons and
                # this decision could be revisited in the future,
                # especially for PythonTest instances.
                if result.addFailure(self, str(e)):
                    success = True
            except Exception:
                result.addError(self, sys.exc_info())
            else:
                success = True

            try:
                self.tearDown()
            except (KeyboardInterrupt, SystemExit):
                self._aborted = True
                raise
            except Exception:
                result.addError(self, sys.exc_info())
                success = False

            if success:
                result.addSuccess(self)
        finally:
            result.stopTest(self, interrupted=self._aborted)

    def runTest(self):
        """Run this test instance.

        This will return a tuple describing the result of the test.
        """
        env = self._getenv()
        self._genrestoreenv(env)
        self._daemonpids.append(env['DAEMON_PIDS'])
        self._createhgrc(env['HGRCPATH'])

        vlog('# Test', self.name)

        ret, out = self._run(env)
        self._finished = True
        self._ret = ret
        self._out = out

        def describe(ret):
            if ret < 0:
                return 'killed by signal: %d' % -ret
            return 'returned error code %d' % ret

        self._skipped = False

        if ret == self.SKIPPED_STATUS:
            if out is None:  # Debug mode, nothing to parse.
                missing = ['unknown']
                failed = None
            else:
                missing, failed = TTest.parsehghaveoutput(out)

            if not missing:
                missing = ['skipped']

            if failed:
                self.fail('hg have failed checking for %s' % failed[-1])
            else:
                self._skipped = True
                raise unittest.SkipTest(missing[-1])
        elif ret == 'timeout':
            self.fail('timed out')
        elif ret is False:
            self.fail('no result code from test')
        elif out != self._refout:
            # Diff generation may rely on written .err file.
            if (
                (ret != 0 or out != self._refout)
                and not self._skipped
                and not self._debug
            ):
                with open(self.errpath, 'wb') as f:
                    for line in out:
                        f.write(line)

            # The result object handles diff calculation for us.
            with firstlock:
                if self._result.addOutputMismatch(self, ret, out, self._refout):
                    # change was accepted, skip failing
                    return
                if self._first:
                    global firsterror
                    firsterror = True

            if ret:
                msg = 'output changed and ' + describe(ret)
            else:
                msg = 'output changed'

            self.fail(msg)
        elif ret:
            self.fail(describe(ret))

    def tearDown(self):
        """Tasks to perform after run()."""
        for entry in self._daemonpids:
            killdaemons(entry)
        self._daemonpids = []

        if self._keeptmpdir:
            log(
                '\nKeeping testtmp dir: %s\nKeeping threadtmp dir: %s'
                % (
                    self._testtmp.decode('utf-8'),
                    self._threadtmp.decode('utf-8'),
                )
            )
        else:
            try:
                shutil.rmtree(self._testtmp)
            except OSError:
                # unreadable directory may be left in $TESTTMP; fix permission
                # and try again
                makecleanable(self._testtmp)
                shutil.rmtree(self._testtmp, True)
            shutil.rmtree(self._threadtmp, True)

        if self._usechg:
            # chgservers will stop automatically after they find the socket
            # files are deleted
            shutil.rmtree(self._chgsockdir, True)

        if (
            (self._ret != 0 or self._out != self._refout)
            and not self._skipped
            and not self._debug
            and self._out
        ):
            with open(self.errpath, 'wb') as f:
                for line in self._out:
                    f.write(line)

        vlog("# Ret was:", self._ret, '(%s)' % self.name)

    def _run(self, env):
        # This should be implemented in child classes to run tests.
        raise unittest.SkipTest('unknown test type')

    def abort(self):
        """Terminate execution of this test."""
        self._aborted = True

    def _portmap(self, i):
        offset = b'' if i == 0 else b'%d' % i
        return (br':%d\b' % (self._startport + i), b':$HGPORT%s' % offset)

    def _getreplacements(self):
        """Obtain a mapping of text replacements to apply to test output.

        Test output needs to be normalized so it can be compared to expected
        output. This function defines how some of that normalization will
        occur.
        """
        # TRACKING MOZ - 9 ports, LOCALHOST
        r = [
            # This list should be parallel to defineport in _getenv
            self._portmap(0),
            self._portmap(1),
            self._portmap(2),
            self._portmap(3),
            self._portmap(4),
            self._portmap(5),
            self._portmap(6),
            self._portmap(7),
            self._portmap(8),
            (br'([^0-9])%s' % re.escape(self._localip()), br'\1$LOCALIP'),
            (br'\bHG_TXNID=TXN:[a-f0-9]{40}\b', br'HG_TXNID=TXN:$ID$'),
        ] + [
            (br'\b%s\b' % re.escape(hostname), br'$LOCALHOST')
            for hostname in
            # Sort by most '.' characters first so that we properly handle
            # aliases that are substrings.
            sorted(self._localhostnames(), key=lambda x: x.count(b'.'), reverse=True)
        ]
        r.append((self._escapepath(self._testtmp), b'$TESTTMP'))

        # TRACKING MOZ - docker stuff
        if 'DOCKER_HOSTNAME' in os.environ:
            r.append((re.escape(os.environ['DOCKER_HOSTNAME'].encode('utf-8')),
                      b'$DOCKER_HOSTNAME'))

        replacementfile = os.path.join(self._testdir, b'common-pattern.py')

        if os.path.exists(replacementfile):
            data = {}
            with open(replacementfile, mode='rb') as source:
                # the intermediate 'compile' step help with debugging
                code = compile(source.read(), replacementfile, 'exec')
                exec(code, data)
                for value in data.get('substitutions', ()):
                    if len(value) != 2:
                        msg = 'malformatted substitution in %s: %r'
                        msg %= (replacementfile, value)
                        raise ValueError(msg)
                    r.append(value)
        return r

    def _escapepath(self, p):
        if os.name == 'nt':
            return b''.join(
                c.isalpha()
                and b'[%s%s]' % (c.lower(), c.upper())
                or c in b'/\\'
                and br'[/\\]'
                or c.isdigit()
                and c
                or b'\\' + c
                for c in [p[i : i + 1] for i in range(len(p))]
            )
        else:
            return re.escape(p)

    def _localip(self):
        if self._useipv6:
            return b'::1'
        else:
            return b'127.0.0.1'

    # Tracking MOZ - add _localhostname for cross-platform compat
    def _localhostname(self):
        return self._localhostnames()[0]

    # Tracking MOZ - add _localhostnames for cross-platform compat
    def _localhostnames(self):
        hostname, aliaslist, _ = socket.gethostbyaddr(self._localip())
        return [
            bytes(alias.encode('utf-8'))
            for alias in [hostname] + aliaslist
        ]

    def _genrestoreenv(self, testenv):
        """Generate a script that can be used by tests to restore the original
        environment."""
        # Put the restoreenv script inside self._threadtmp
        scriptpath = os.path.join(self._threadtmp, b'restoreenv.sh')
        testenv['HGTEST_RESTOREENV'] = _strpath(scriptpath)

        # Only restore environment variable names that the shell allows
        # us to export.
        name_regex = re.compile('^[a-zA-Z][a-zA-Z0-9_]*$')

        # Do not restore these variables; otherwise tests would fail.
        reqnames = {'PYTHON', 'TESTDIR', 'TESTTMP'}

        with open(scriptpath, 'w') as envf:
            for name, value in origenviron.items():
                if not name_regex.match(name):
                    # Skip environment variables with unusual names not
                    # allowed by most shells.
                    continue
                if name in reqnames:
                    continue
                envf.write('%s=%s\n' % (name, shellquote(value)))

            for name in testenv:
                if name in origenviron or name in reqnames:
                    continue
                envf.write('unset %s\n' % (name,))

    def _getenv(self):
        """Obtain environment variables to use during test execution."""

        def defineport(i):
            offset = '' if i == 0 else '%s' % i
            env["HGPORT%s" % offset] = '%s' % (self._startport + i)

        env = os.environ.copy()
        env['PYTHONUSERBASE'] = sysconfig.get_config_var('userbase') or ''
        # TRACKING MOZ - add ERR_FILE and set 9 ports
        env['HGEMITWARNINGS'] = '1'
        env['TESTTMP'] = _strpath(self._testtmp)
        env['TESTNAME'] = self.name
        env['HOME'] = _strpath(self._testtmp)
        # This number should match portneeded in _getport
        for port in xrange(9):
            # This list should be parallel to _portmap in _getreplacements
            defineport(port)
        env["HGRCPATH"] = _strpath(os.path.join(self._threadtmp, b'.hgrc'))
        env["DAEMON_PIDS"] = _strpath(
            os.path.join(self._threadtmp, b'daemon.pids')
        )
        env["HGEDITOR"] = (
            '"' + sysexecutable + '"' + ' -c "import sys; sys.exit(0)"'
        )
        env["HGUSER"] = "test"
        env["HGENCODING"] = "ascii"
        env["HGENCODINGMODE"] = "strict"
        env["HGHOSTNAME"] = "test-hostname"
        env['HGIPV6'] = str(int(self._useipv6))
        env["ERR_FILE"] = self.errpath
        # See contrib/catapipe.py for how to use this functionality.
        if 'HGTESTCATAPULTSERVERPIPE' not in env:
            # If we don't have HGTESTCATAPULTSERVERPIPE explicitly set, pull the
            # non-test one in as a default, otherwise set to devnull
            env['HGTESTCATAPULTSERVERPIPE'] = env.get(
                'HGCATAPULTSERVERPIPE', os.devnull
            )

        extraextensions = []
        for opt in self._extraconfigopts:
            section, key = opt.encode('utf-8').split(b'.', 1)
            if section != 'extensions':
                continue
            name = key.split(b'=', 1)[0]
            extraextensions.append(name)

        if extraextensions:
            env['HGTESTEXTRAEXTENSIONS'] = b' '.join(extraextensions)

        # LOCALIP could be ::1 or 127.0.0.1. Useful for tests that require raw
        # IP addresses.
        env['LOCALIP'] = _strpath(self._localip())

        # TRACKING MOZ - set LOCALHOST for cross-platform localhost naming
        env['LOCALHOST'] = _strpath(self._localhostname())

        # This has the same effect as Py_LegacyWindowsStdioFlag in exewrapper.c,
        # but this is needed for testing python instances like dummyssh,
        # dummysmtpd.py, and dumbhttp.py.
        if PYTHON3 and os.name == 'nt':
            env['PYTHONLEGACYWINDOWSSTDIO'] = '1'

        # Modified HOME in test environment can confuse Rust tools. So set
        # CARGO_HOME and RUSTUP_HOME automatically if a Rust toolchain is
        # present and these variables aren't already defined.
        cargo_home_path = os.path.expanduser('~/.cargo')
        rustup_home_path = os.path.expanduser('~/.rustup')

        if os.path.exists(cargo_home_path) and b'CARGO_HOME' not in osenvironb:
            env['CARGO_HOME'] = cargo_home_path
        if (
            os.path.exists(rustup_home_path)
            and b'RUSTUP_HOME' not in osenvironb
        ):
            env['RUSTUP_HOME'] = rustup_home_path

        # Reset some environment variables to well-known values so that
        # the tests produce repeatable output.
        env['LANG'] = env['LC_ALL'] = env['LANGUAGE'] = 'C'
        env['TZ'] = 'GMT'
        env["EMAIL"] = "Foo Bar <foo.bar@example.com>"
        env['COLUMNS'] = '80'
        env['TERM'] = 'xterm'

        dropped = [
            'CDPATH',
            'CHGDEBUG',
            'EDITOR',
            'GREP_OPTIONS',
            'HG',
            'HGMERGE',
            'HGPLAIN',
            'HGPLAINEXCEPT',
            'HGPROF',
            'http_proxy',
            'no_proxy',
            'NO_PROXY',
            'PAGER',
            'VISUAL',
        ]

        for k in dropped:
            if k in env:
                del env[k]

        # unset env related to hooks
        for k in list(env):
            if k.startswith('HG_'):
                del env[k]

        if self._usechg:
            env['CHGSOCKNAME'] = os.path.join(self._chgsockdir, b'server')

        return env

    def _createhgrc(self, path):
        """Create an hgrc file for this test."""
        with open(path, 'wb') as hgrc:
            hgrc.write(b'[ui]\n')
            hgrc.write(b'slash = True\n')
            hgrc.write(b'interactive = False\n')
            hgrc.write(b'merge = internal:merge\n')
            hgrc.write(b'mergemarkers = detailed\n')
            hgrc.write(b'promptecho = True\n')
            hgrc.write(b'[defaults]\n')
            hgrc.write(b'[devel]\n')
            hgrc.write(b'all-warnings = true\n')
            hgrc.write(b'default-date = 0 0\n')
            hgrc.write(b'[largefiles]\n')
            hgrc.write(
                b'usercache = %s\n'
                % (os.path.join(self._testtmp, b'.cache/largefiles'))
            )
            hgrc.write(b'[lfs]\n')
            hgrc.write(
                b'usercache = %s\n'
                % (os.path.join(self._testtmp, b'.cache/lfs'))
            )
            hgrc.write(b'[web]\n')
            hgrc.write(b'address = localhost\n')
            hgrc.write(b'ipv6 = %s\n' % str(self._useipv6).encode('ascii'))
            hgrc.write(b'server-header = testing stub value\n')

            for opt in self._extraconfigopts:
                section, key = opt.encode('utf-8').split(b'.', 1)
                assert b'=' in key, (
                    'extra config opt %s must ' 'have an = for assignment' % opt
                )
                hgrc.write(b'[%s]\n%s\n' % (section, key))

    def fail(self, msg):
        # unittest differentiates between errored and failed.
        # Failed is denoted by AssertionError (by default at least).
        raise AssertionError(msg)

    def _runcommand(self, cmd, env, normalizenewlines=False):
        """Run command in a sub-process, capturing the output (stdout and
        stderr).

        Return a tuple (exitcode, output). output is None in debug mode.
        """
        if self._debug:
            proc = subprocess.Popen(
                _strpath(cmd), shell=True, cwd=_strpath(self._testtmp), env=env
            )
            ret = proc.wait()
            return (ret, None)

        proc = Popen4(cmd, self._testtmp, self._timeout, env)

        def cleanup():
            terminate(proc)
            ret = proc.wait()
            if ret == 0:
                ret = signal.SIGTERM << 8
            killdaemons(env['DAEMON_PIDS'])
            return ret

        proc.tochild.close()

        try:
            output = proc.fromchild.read()
        except KeyboardInterrupt:
            vlog('# Handling keyboard interrupt')
            cleanup()
            raise

        ret = proc.wait()
        if wifexited(ret):
            ret = os.WEXITSTATUS(ret)

        if proc.timeout:
            ret = 'timeout'

        if ret:
            killdaemons(env['DAEMON_PIDS'])

        for s, r in self._getreplacements():
            output = re.sub(s, r, output)

        if normalizenewlines:
            output = output.replace(b'\r\n', b'\n')

        return ret, output.splitlines(True)


class PythonTest(Test):
    """A Python-based test."""

    @property
    def refpath(self):
        return os.path.join(self._testdir, b'%s.out' % self.bname)

    def _run(self, env):
        py3switch = self._py3warnings and b' -3' or b''
        # Quote the python(3) executable for Windows
        cmd = b'"%s"%s "%s"' % (PYTHON, py3switch, self.path)
        vlog("# Running", cmd.decode("utf-8"))
        normalizenewlines = os.name == 'nt'
        result = self._runcommand(cmd, env, normalizenewlines=normalizenewlines)
        if self._aborted:
            raise KeyboardInterrupt()

        return result


# Some glob patterns apply only in some circumstances, so the script
# might want to remove (glob) annotations that otherwise should be
# retained.
checkcodeglobpats = [
    # On Windows it looks like \ doesn't require a (glob), but we know
    # better.
    re.compile(br'^pushing to \$TESTTMP/.*[^)]$'),
    re.compile(br'^moving \S+/.*[^)]$'),
    re.compile(br'^pulling from \$TESTTMP/.*[^)]$'),
    # Not all platforms have 127.0.0.1 as loopback (though most do),
    # so we always glob that too.
    re.compile(br'.*\$LOCALIP.*$'),
]

bchr = chr
if PYTHON3:
    bchr = lambda x: bytes([x])

WARN_UNDEFINED = 1
WARN_YES = 2
WARN_NO = 3

MARK_OPTIONAL = b" (?)\n"


def isoptional(line):
    return line.endswith(MARK_OPTIONAL)


class TTest(Test):
    """A "t test" is a test backed by a .t file."""

    SKIPPED_PREFIX = b'skipped: '
    FAILED_PREFIX = b'hghave check failed: '
    NEEDESCAPE = re.compile(br'[\x00-\x08\x0b-\x1f\x7f-\xff]').search

    ESCAPESUB = re.compile(br'[\x00-\x08\x0b-\x1f\\\x7f-\xff]').sub
    ESCAPEMAP = dict((bchr(i), br'\x%02x' % i) for i in range(256))
    ESCAPEMAP.update({b'\\': b'\\\\', b'\r': br'\r'})

    def __init__(self, path, *args, **kwds):
        # accept an extra "case" parameter
        case = kwds.pop('case', [])
        self._case = case
        self._allcases = {x for y in parsettestcases(path) for x in y}
        super(TTest, self).__init__(path, *args, **kwds)
        if case:
            casepath = b'#'.join(case)
            self.name = '%s#%s' % (self.name, _strpath(casepath))
            self.errpath = b'%s#%s.err' % (self.errpath[:-4], casepath)
            self._tmpname += b'-%s' % casepath
        self._have = {}

    @property
    def refpath(self):
        return os.path.join(self._testdir, self.bname)

    def _run(self, env):
        with open(self.path, 'rb') as f:
            lines = f.readlines()

        # .t file is both reference output and the test input, keep reference
        # output updated with the the test input. This avoids some race
        # conditions where the reference output does not match the actual test.
        if self._refout is not None:
            self._refout = lines

        salt, script, after, expected = self._parsetest(lines)

        # Write out the generated script.
        fname = b'%s.sh' % self._testtmp
        with open(fname, 'wb') as f:
            for l in script:
                f.write(l)

        cmd = b'%s "%s"' % (self._shell, fname)
        vlog("# Running", cmd.decode("utf-8"))

        exitcode, output = self._runcommand(cmd, env)

        if self._aborted:
            raise KeyboardInterrupt()

        # Do not merge output if skipped. Return hghave message instead.
        # Similarly, with --debug, output is None.
        if exitcode == self.SKIPPED_STATUS or output is None:
            return exitcode, output

        return self._processoutput(exitcode, output, salt, after, expected)

    def _hghave(self, reqs):
        allreqs = b' '.join(reqs)

        self._detectslow(reqs)

        if allreqs in self._have:
            return self._have.get(allreqs)

        # TRACKING MOZ
        # use custom hghave and use instead of tdir
        hghave_path = os.path.join(REPO_ROOT, 'testing', 'hghave.py')

        # TODO do something smarter when all other uses of hghave are gone.
        runtestdir = osenvironb[b'RUNTESTDIR']
        tdir = runtestdir.replace(b'\\', b'/')
        proc = Popen4(
            b'%s %s' % (hghave_path.encode('utf-8'), allreqs),
            self._testtmp,
            0,
            self._getenv(),
        )
        stdout, stderr = proc.communicate()
        ret = proc.wait()
        if wifexited(ret):
            ret = os.WEXITSTATUS(ret)
        if ret == 2:
            print(stdout.decode('utf-8'))
            sys.exit(1)

        if ret != 0:
            self._have[allreqs] = (False, stdout)
            return False, stdout

        self._have[allreqs] = (True, None)
        return True, None

    def _detectslow(self, reqs):
        """update the timeout of slow test when appropriate"""
        if b'slow' in reqs:
            self._timeout = self._slowtimeout

    def _iftest(self, args):
        # implements "#if"
        reqs = []
        for arg in args:
            if arg.startswith(b'no-') and arg[3:] in self._allcases:
                if arg[3:] in self._case:
                    return False
            elif arg in self._allcases:
                if arg not in self._case:
                    return False
            else:
                reqs.append(arg)
        self._detectslow(reqs)
        return self._hghave(reqs)[0]

    def _parsetest(self, lines):
        # We generate a shell script which outputs unique markers to line
        # up script results with our source. These markers include input
        # line number and the last return code.
        salt = b"SALT%d" % time.time()

        def addsalt(line, inpython):
            if inpython:
                script.append(b'%s %d 0\n' % (salt, line))
            else:
                script.append(b'echo %s %d $?\n' % (salt, line))

        activetrace = []
        session = str(uuid.uuid4())
        if PYTHON3:
            session = session.encode('ascii')
        hgcatapult = os.getenv('HGTESTCATAPULTSERVERPIPE') or os.getenv(
            'HGCATAPULTSERVERPIPE'
        )

        def toggletrace(cmd=None):
            if not hgcatapult or hgcatapult == os.devnull:
                return

            if activetrace:
                script.append(
                    b'echo END %s %s >> "$HGTESTCATAPULTSERVERPIPE"\n'
                    % (session, activetrace[0])
                )
            if cmd is None:
                return

            if isinstance(cmd, str):
                quoted = shellquote(cmd.strip())
            else:
                quoted = shellquote(cmd.strip().decode('utf8')).encode('utf8')
            quoted = quoted.replace(b'\\', b'\\\\')
            script.append(
                b'echo START %s %s >> "$HGTESTCATAPULTSERVERPIPE"\n'
                % (session, quoted)
            )
            activetrace[0:] = [quoted]

        script = []

        # After we run the shell script, we re-unify the script output
        # with non-active parts of the source, with synchronization by our
        # SALT line number markers. The after table contains the non-active
        # components, ordered by line number.
        after = {}

        # Expected shell script output.
        expected = {}

        pos = prepos = -1

        # True or False when in a true or false conditional section
        skipping = None

        # We keep track of whether or not we're in a Python block so we
        # can generate the surrounding doctest magic.
        inpython = False

        if self._debug:
            script.append(b'set -x\n')
        if self._hgcommand != b'hg':
            script.append(b'alias hg="%s"\n' % self._hgcommand)
        if os.getenv('MSYSTEM'):
            script.append(b'alias pwd="pwd -W"\n')

        if hgcatapult and hgcatapult != os.devnull:
            if PYTHON3:
                hgcatapult = hgcatapult.encode('utf8')
                cataname = self.name.encode('utf8')
            else:
                cataname = self.name

            # Kludge: use a while loop to keep the pipe from getting
            # closed by our echo commands. The still-running file gets
            # reaped at the end of the script, which causes the while
            # loop to exit and closes the pipe. Sigh.
            script.append(
                b'rtendtracing() {\n'
                b'  echo END %(session)s %(name)s >> %(catapult)s\n'
                b'  rm -f "$TESTTMP/.still-running"\n'
                b'}\n'
                b'trap "rtendtracing" 0\n'
                b'touch "$TESTTMP/.still-running"\n'
                b'while [ -f "$TESTTMP/.still-running" ]; do sleep 1; done '
                b'> %(catapult)s &\n'
                b'HGCATAPULTSESSION=%(session)s ; export HGCATAPULTSESSION\n'
                b'echo START %(session)s %(name)s >> %(catapult)s\n'
                % {
                    b'name': cataname,
                    b'session': session,
                    b'catapult': hgcatapult,
                }
            )

        if self._case:
            casestr = b'#'.join(self._case)
            if isinstance(casestr, str):
                quoted = shellquote(casestr)
            else:
                quoted = shellquote(casestr.decode('utf8')).encode('utf8')
            script.append(b'TESTCASE=%s\n' % quoted)
            script.append(b'export TESTCASE\n')

        n = 0
        for n, l in enumerate(lines):
            if not l.endswith(b'\n'):
                l += b'\n'
            if l.startswith(b'#require'):
                lsplit = l.split()
                if len(lsplit) < 2 or lsplit[0] != b'#require':
                    after.setdefault(pos, []).append(
                        b'  !!! invalid #require\n'
                    )
                if not skipping:
                    haveresult, message = self._hghave(lsplit[1:])
                    if not haveresult:
                        script = [b'echo "%s"\nexit 80\n' % message]
                        break
                after.setdefault(pos, []).append(l)
            elif l.startswith(b'#if'):
                lsplit = l.split()
                if len(lsplit) < 2 or lsplit[0] != b'#if':
                    after.setdefault(pos, []).append(b'  !!! invalid #if\n')
                if skipping is not None:
                    after.setdefault(pos, []).append(b'  !!! nested #if\n')
                skipping = not self._iftest(lsplit[1:])
                after.setdefault(pos, []).append(l)
            elif l.startswith(b'#else'):
                if skipping is None:
                    after.setdefault(pos, []).append(b'  !!! missing #if\n')
                skipping = not skipping
                after.setdefault(pos, []).append(l)
            elif l.startswith(b'#endif'):
                if skipping is None:
                    after.setdefault(pos, []).append(b'  !!! missing #if\n')
                skipping = None
                after.setdefault(pos, []).append(l)
            elif skipping:
                after.setdefault(pos, []).append(l)
            elif l.startswith(b'  >>> '):  # python inlines
                after.setdefault(pos, []).append(l)
                prepos = pos
                pos = n
                if not inpython:
                    # We've just entered a Python block. Add the header.
                    inpython = True
                    addsalt(prepos, False)  # Make sure we report the exit code.
                    script.append(b'"%s" -m heredoctest <<EOF\n' % PYTHON)
                addsalt(n, True)
                script.append(l[2:])
            elif l.startswith(b'  ... '):  # python inlines
                after.setdefault(prepos, []).append(l)
                script.append(l[2:])
            elif l.startswith(b'  $ '):  # commands
                if inpython:
                    script.append(b'EOF\n')
                    inpython = False
                after.setdefault(pos, []).append(l)
                prepos = pos
                pos = n
                addsalt(n, False)
                rawcmd = l[4:]
                cmd = rawcmd.split()
                toggletrace(rawcmd)
                if len(cmd) == 2 and cmd[0] == b'cd':
                    rawcmd = b'cd %s || exit 1\n' % cmd[1]
                script.append(rawcmd)
            elif l.startswith(b'  > '):  # continuations
                after.setdefault(prepos, []).append(l)
                script.append(l[4:])
            elif l.startswith(b'  '):  # results
                # Queue up a list of expected results.
                expected.setdefault(pos, []).append(l[2:])
            else:
                if inpython:
                    script.append(b'EOF\n')
                    inpython = False
                # Non-command/result. Queue up for merged output.
                after.setdefault(pos, []).append(l)

        if inpython:
            script.append(b'EOF\n')
        if skipping is not None:
            after.setdefault(pos, []).append(b'  !!! missing #endif\n')
        addsalt(n + 1, False)
        # Need to end any current per-command trace
        if activetrace:
            toggletrace()
        return salt, script, after, expected

    def _processoutput(self, exitcode, output, salt, after, expected):
        # Merge the script output back into a unified test.
        warnonly = WARN_UNDEFINED  # 1: not yet; 2: yes; 3: for sure not
        if exitcode != 0:
            warnonly = WARN_NO

        pos = -1
        postout = []
        for out_rawline in output:
            out_line, cmd_line = out_rawline, None
            if salt in out_rawline:
                out_line, cmd_line = out_rawline.split(salt, 1)

            pos, postout, warnonly = self._process_out_line(
                out_line, pos, postout, expected, warnonly
            )
            pos, postout = self._process_cmd_line(cmd_line, pos, postout, after)

        if pos in after:
            postout += after.pop(pos)

        if warnonly == WARN_YES:
            exitcode = False  # Set exitcode to warned.

        return exitcode, postout

    def _process_out_line(self, out_line, pos, postout, expected, warnonly):
        while out_line:
            if not out_line.endswith(b'\n'):
                out_line += b' (no-eol)\n'

            # Find the expected output at the current position.
            els = [None]
            if expected.get(pos, None):
                els = expected[pos]

            optional = []
            for i, el in enumerate(els):
                r = False
                if el:
                    r, exact = self.linematch(el, out_line)
                if isinstance(r, str):
                    if r == '-glob':
                        out_line = ''.join(el.rsplit(' (glob)', 1))
                        r = ''  # Warn only this line.
                    elif r == "retry":
                        postout.append(b'  ' + el)
                    else:
                        log('\ninfo, unknown linematch result: %r\n' % r)
                        r = False
                if r:
                    els.pop(i)
                    break
                if el:
                    if isoptional(el):
                        optional.append(i)
                    else:
                        m = optline.match(el)
                        if m:
                            conditions = [c for c in m.group(2).split(b' ')]

                            if not self._iftest(conditions):
                                optional.append(i)
                    if exact:
                        # Don't allow line to be matches against a later
                        # line in the output
                        els.pop(i)
                        break

            if r:
                if r == "retry":
                    continue
                # clean up any optional leftovers
                for i in optional:
                    postout.append(b'  ' + els[i])
                for i in reversed(optional):
                    del els[i]
                postout.append(b'  ' + el)
            else:
                if self.NEEDESCAPE(out_line):
                    out_line = TTest._stringescape(
                        b'%s (esc)\n' % out_line.rstrip(b'\n')
                    )
                postout.append(b'  ' + out_line)  # Let diff deal with it.
                if r != '':  # If line failed.
                    warnonly = WARN_NO
                elif warnonly == WARN_UNDEFINED:
                    warnonly = WARN_YES
            break
        else:
            # clean up any optional leftovers
            while expected.get(pos, None):
                el = expected[pos].pop(0)
                if el:
                    if not isoptional(el):
                        m = optline.match(el)
                        if m:
                            conditions = [c for c in m.group(2).split(b' ')]

                            if self._iftest(conditions):
                                # Don't append as optional line
                                continue
                        else:
                            continue
                postout.append(b'  ' + el)
        return pos, postout, warnonly

    def _process_cmd_line(self, cmd_line, pos, postout, after):
        """process a "command" part of a line from unified test output"""
        if cmd_line:
            # Add on last return code.
            ret = int(cmd_line.split()[1])
            if ret != 0:
                postout.append(b'  [%d]\n' % ret)
            if pos in after:
                # Merge in non-active test bits.
                postout += after.pop(pos)
            pos = int(cmd_line.split()[0])
        return pos, postout

    @staticmethod
    def rematch(el, l):
        try:
            # parse any flags at the beginning of the regex. Only 'i' is
            # supported right now, but this should be easy to extend.
            flags, el = re.match(br'^(\(\?i\))?(.*)', el).groups()[0:2]
            flags = flags or b''
            el = flags + b'(?:' + el + b')'
            # use \Z to ensure that the regex matches to the end of the string
            if os.name == 'nt':
                return re.match(el + br'\r?\n\Z', l)
            return re.match(el + br'\n\Z', l)
        except re.error:
            # el is an invalid regex
            return False

    @staticmethod
    def globmatch(el, l):
        # The only supported special characters are * and ? plus / which also
        # matches \ on windows. Escaping of these characters is supported.
        if el + b'\n' == l:
            if os.altsep:
                # matching on "/" is not needed for this line
                for pat in checkcodeglobpats:
                    if pat.match(el):
                        return True
                return b'-glob'
            return True
        el = el.replace(b'$LOCALIP', b'*')
        i, n = 0, len(el)
        res = b''
        while i < n:
            c = el[i : i + 1]
            i += 1
            if c == b'\\' and i < n and el[i : i + 1] in b'*?\\/':
                res += el[i - 1 : i + 1]
                i += 1
            elif c == b'*':
                res += b'.*'
            elif c == b'?':
                res += b'.'
            elif c == b'/' and os.altsep:
                res += b'[/\\\\]'
            else:
                res += re.escape(c)
        return TTest.rematch(res, l)

    def linematch(self, el, l):
        if el == l:  # perfect match (fast)
            return True, True
        retry = False
        if isoptional(el):
            retry = "retry"
            el = el[: -len(MARK_OPTIONAL)] + b"\n"
        else:
            m = optline.match(el)
            if m:
                conditions = [c for c in m.group(2).split(b' ')]

                el = m.group(1) + b"\n"
                if not self._iftest(conditions):
                    # listed feature missing, should not match
                    return "retry", False

        if el.endswith(b" (esc)\n"):
            if PYTHON3:
                el = el[:-7].decode('unicode_escape') + '\n'
                el = el.encode('utf-8')
            else:
                el = el[:-7].decode('string-escape') + '\n'
        if el == l or os.name == 'nt' and el[:-1] + b'\r\n' == l:
            return True, True
        if el.endswith(b" (re)\n"):
            return (TTest.rematch(el[:-6], l) or retry), False
        if el.endswith(b" (glob)\n"):
            # ignore '(glob)' added to l by 'replacements'
            if l.endswith(b" (glob)\n"):
                l = l[:-8] + b"\n"
            return (TTest.globmatch(el[:-8], l) or retry), False
        if os.altsep:
            _l = l.replace(b'\\', b'/')
            if el == _l or os.name == 'nt' and el[:-1] + b'\r\n' == _l:
                return True, True
        return retry, True

    @staticmethod
    def parsehghaveoutput(lines):
        '''Parse hghave log lines.

        Return tuple of lists (missing, failed):
          * the missing/unknown features
          * the features for which existence check failed'''
        missing = []
        failed = []
        for line in lines:
            if line.startswith(TTest.SKIPPED_PREFIX):
                line = line.splitlines()[0]
                missing.append(
                    line[len(TTest.SKIPPED_PREFIX) :].decode('utf-8')
                )
            elif line.startswith(TTest.FAILED_PREFIX):
                line = line.splitlines()[0]
                failed.append(line[len(TTest.FAILED_PREFIX) :].decode('utf-8'))

        return missing, failed

    @staticmethod
    def _escapef(m):
        return TTest.ESCAPEMAP[m.group(0)]

    @staticmethod
    def _stringescape(s):
        return TTest.ESCAPESUB(TTest._escapef, s)


iolock = threading.RLock()
firstlock = threading.RLock()
firsterror = False


class TestResult(unittest._TextTestResult):
    """Holds results when executing via unittest."""

    # Don't worry too much about accessing the non-public _TextTestResult.
    # It is relatively common in Python testing tools.
    def __init__(self, options, *args, **kwargs):
        super(TestResult, self).__init__(*args, **kwargs)

        self._options = options

        # unittest.TestResult didn't have skipped until 2.7. We need to
        # polyfill it.
        self.skipped = []

        # We have a custom "ignored" result that isn't present in any Python
        # unittest implementation. It is very similar to skipped. It may make
        # sense to map it into skip some day.
        self.ignored = []

        self.times = []
        self._firststarttime = None
        # Data stored for the benefit of generating xunit reports.
        self.successes = []
        self.faildata = {}

        if options.color == 'auto':
            self.color = pygmentspresent and self.stream.isatty()
        elif options.color == 'never':
            self.color = False
        else:  # 'always', for testing purposes
            self.color = pygmentspresent

    def onStart(self, test):
        """ Can be overriden by custom TestResult
        """

    def onEnd(self):
        """ Can be overriden by custom TestResult
        """

    def addFailure(self, test, reason):
        self.failures.append((test, reason))

        if self._options.first:
            self.stop()
        else:
            with iolock:
                if reason == "timed out":
                    self.stream.write('t')
                else:
                    if not self._options.nodiff:
                        self.stream.write('\n')
                        # Exclude the '\n' from highlighting to lex correctly
                        formatted = 'ERROR: %s output changed\n' % test
                        self.stream.write(highlightmsg(formatted, self.color))
                    self.stream.write('!')

                self.stream.flush()

    def addSuccess(self, test):
        with iolock:
            super(TestResult, self).addSuccess(test)
        self.successes.append(test)

    def addError(self, test, err):
        super(TestResult, self).addError(test, err)
        if self._options.first:
            self.stop()

    # Polyfill.
    def addSkip(self, test, reason):
        self.skipped.append((test, reason))
        with iolock:
            if self.showAll:
                self.stream.writeln('skipped %s' % reason)
            else:
                self.stream.write('s')
                self.stream.flush()

    def addIgnore(self, test, reason):
        self.ignored.append((test, reason))
        with iolock:
            if self.showAll:
                self.stream.writeln('ignored %s' % reason)
            else:
                if reason not in ('not retesting', "doesn't match keyword"):
                    self.stream.write('i')
                else:
                    self.testsRun += 1
                self.stream.flush()

    def addOutputMismatch(self, test, ret, got, expected):
        """Record a mismatch in test output for a particular test."""
        if self.shouldStop or firsterror:
            # don't print, some other test case already failed and
            # printed, we're just stale and probably failed due to our
            # temp dir getting cleaned up.
            return

        accepted = False
        lines = []

        with iolock:
            if self._options.nodiff:
                pass
            elif self._options.view:
                v = self._options.view
                subprocess.call(
                    r'"%s" "%s" "%s"'
                    % (v, _strpath(test.refpath), _strpath(test.errpath)),
                    shell=True,
                )
            else:
                servefail, lines = getdiff(
                    expected, got, test.refpath, test.errpath
                )
                self.stream.write('\n')
                for line in lines:
                    line = highlightdiff(line, self.color)
                    if PYTHON3:
                        self.stream.flush()
                        self.stream.buffer.write(line)
                        self.stream.buffer.flush()
                    else:
                        self.stream.write(line)
                        self.stream.flush()

                if servefail:
                    raise test.failureException(
                        'server failed to start (HGPORT=%s)' % test._startport
                    )

            # handle interactive prompt without releasing iolock
            if self._options.interactive:
                if test.readrefout() != expected:
                    self.stream.write(
                        'Reference output has changed (run again to prompt '
                        'changes)'
                    )
                else:
                    self.stream.write('Accept this change? [n] ')
                    self.stream.flush()
                    answer = sys.stdin.readline().strip()
                    if answer.lower() in ('y', 'yes'):
                        if test.path.endswith(b'.t'):
                            rename(test.errpath, test.path)
                        else:
                            rename(test.errpath, '%s.out' % test.path)
                        accepted = True
            if not accepted:
                self.faildata[test.name] = b''.join(lines)

        return accepted

    def startTest(self, test):
        super(TestResult, self).startTest(test)

        # os.times module computes the user time and system time spent by
        # child's processes along with real elapsed time taken by a process.
        # This module has one limitation. It can only work for Linux user
        # and not for Windows. Hence why we fall back to another function
        # for wall time calculations.
        test.started_times = os.times()
        # TODO use a monotonic clock once support for Python 2.7 is dropped.
        test.started_time = time.time()
        if self._firststarttime is None:  # thread racy but irrelevant
            self._firststarttime = test.started_time

    def stopTest(self, test, interrupted=False):
        super(TestResult, self).stopTest(test)

        test.stopped_times = os.times()
        stopped_time = time.time()

        starttime = test.started_times
        endtime = test.stopped_times
        origin = self._firststarttime
        self.times.append(
            (
                test.name,
                endtime[2] - starttime[2],  # user space CPU time
                endtime[3] - starttime[3],  # sys  space CPU time
                stopped_time - test.started_time,  # real time
                test.started_time - origin,  # start date in run context
                stopped_time - origin,  # end date in run context
            )
        )

        if interrupted:
            with iolock:
                self.stream.writeln(
                    'INTERRUPTED: %s (after %d seconds)'
                    % (test.name, self.times[-1][3])
                )


def getTestResult():
    """
    Returns the relevant test result
    """
    if "CUSTOM_TEST_RESULT" in os.environ:
        testresultmodule = __import__(os.environ["CUSTOM_TEST_RESULT"])
        return testresultmodule.TestResult
    else:
        return TestResult


class TestSuite(unittest.TestSuite):
    """Custom unittest TestSuite that knows how to execute Mercurial tests."""

    def __init__(
        self,
        testdir,
        jobs=1,
        whitelist=None,
        blacklist=None,
        retest=False,
        keywords=None,
        loop=False,
        runs_per_test=1,
        loadtest=None,
        showchannels=False,
        *args,
        **kwargs
    ):
        """Create a new instance that can run tests with a configuration.

        testdir specifies the directory where tests are executed from. This
        is typically the ``tests`` directory from Mercurial's source
        repository.

        jobs specifies the number of jobs to run concurrently. Each test
        executes on its own thread. Tests actually spawn new processes, so
        state mutation should not be an issue.

        If there is only one job, it will use the main thread.

        whitelist and blacklist denote tests that have been whitelisted and
        blacklisted, respectively. These arguments don't belong in TestSuite.
        Instead, whitelist and blacklist should be handled by the thing that
        populates the TestSuite with tests. They are present to preserve
        backwards compatible behavior which reports skipped tests as part
        of the results.

        retest denotes whether to retest failed tests. This arguably belongs
        outside of TestSuite.

        keywords denotes key words that will be used to filter which tests
        to execute. This arguably belongs outside of TestSuite.

        loop denotes whether to loop over tests forever.
        """
        super(TestSuite, self).__init__(*args, **kwargs)

        self._jobs = jobs
        self._whitelist = whitelist
        self._blacklist = blacklist
        self._retest = retest
        self._keywords = keywords
        self._loop = loop
        self._runs_per_test = runs_per_test
        self._loadtest = loadtest
        self._showchannels = showchannels

    def run(self, result):
        # We have a number of filters that need to be applied. We do this
        # here instead of inside Test because it makes the running logic for
        # Test simpler.
        tests = []
        num_tests = [0]
        for test in self._tests:

            def get():
                num_tests[0] += 1
                if getattr(test, 'should_reload', False):
                    return self._loadtest(test, num_tests[0])
                return test

            if not os.path.exists(test.path):
                result.addSkip(test, "Doesn't exist")
                continue

            if not (self._whitelist and test.bname in self._whitelist):
                if self._blacklist and test.bname in self._blacklist:
                    result.addSkip(test, 'blacklisted')
                    continue

                if self._retest and not os.path.exists(test.errpath):
                    result.addIgnore(test, 'not retesting')
                    continue

                if self._keywords:
                    with open(test.path, 'rb') as f:
                        t = f.read().lower() + test.bname.lower()
                    ignored = False
                    for k in self._keywords.lower().split():
                        if k not in t:
                            result.addIgnore(test, "doesn't match keyword")
                            ignored = True
                            break

                    if ignored:
                        continue
            for _ in xrange(self._runs_per_test):
                tests.append(get())

        runtests = list(tests)
        done = queue.Queue()
        running = 0

        channels = [""] * self._jobs

        def job(test, result):
            for n, v in enumerate(channels):
                if not v:
                    channel = n
                    break
            else:
                raise ValueError('Could not find output channel')
            channels[channel] = "=" + test.name[5:].split(".")[0]
            try:
                test(result)
                done.put(None)
            except KeyboardInterrupt:
                pass
            except:  # re-raises
                done.put(('!', test, 'run-test raised an error, see traceback'))
                raise
            finally:
                try:
                    channels[channel] = ''
                except IndexError:
                    pass

        def stat():
            count = 0
            while channels:
                d = '\n%03s  ' % count
                for n, v in enumerate(channels):
                    if v:
                        d += v[0]
                        channels[n] = v[1:] or '.'
                    else:
                        d += ' '
                    d += ' '
                with iolock:
                    sys.stdout.write(d + '  ')
                    sys.stdout.flush()
                for x in xrange(10):
                    if channels:
                        time.sleep(0.1)
                count += 1

        stoppedearly = False

        if self._showchannels:
            statthread = threading.Thread(target=stat, name="stat")
            statthread.start()

        try:
            while tests or running:
                if not done.empty() or running == self._jobs or not tests:
                    try:
                        done.get(True, 1)
                        running -= 1
                        if result and result.shouldStop:
                            stoppedearly = True
                            break
                    except queue.Empty:
                        continue
                if tests and not running == self._jobs:
                    test = tests.pop(0)
                    if self._loop:
                        if getattr(test, 'should_reload', False):
                            num_tests[0] += 1
                            tests.append(self._loadtest(test, num_tests[0]))
                        else:
                            tests.append(test)
                    if self._jobs == 1:
                        job(test, result)
                    else:
                        t = threading.Thread(
                            target=job, name=test.name, args=(test, result)
                        )
                        t.start()
                    running += 1

            # If we stop early we still need to wait on started tests to
            # finish. Otherwise, there is a race between the test completing
            # and the test's cleanup code running. This could result in the
            # test reporting incorrect.
            if stoppedearly:
                while running:
                    try:
                        done.get(True, 1)
                        running -= 1
                    except queue.Empty:
                        continue
        except KeyboardInterrupt:
            for test in runtests:
                test.abort()

        channels = []

        return result


# Save the most recent 5 wall-clock runtimes of each test to a
# human-readable text file named .testtimes. Tests are sorted
# alphabetically, while times for each test are listed from oldest to
# newest.


def loadtimes(outputdir):
    times = []
    try:
        with open(os.path.join(outputdir, b'.testtimes')) as fp:
            for line in fp:
                m = re.match('(.*?) ([0-9. ]+)', line)
                times.append(
                    (m.group(1), [float(t) for t in m.group(2).split()])
                )
    except IOError as err:
        if err.errno != errno.ENOENT:
            raise
    return times


def savetimes(outputdir, result):
    saved = dict(loadtimes(outputdir))
    maxruns = 5
    skipped = set([str(t[0]) for t in result.skipped])
    for tdata in result.times:
        test, real = tdata[0], tdata[3]
        if test not in skipped:
            ts = saved.setdefault(test, [])
            ts.append(real)
            ts[:] = ts[-maxruns:]

    fd, tmpname = tempfile.mkstemp(
        prefix=b'.testtimes', dir=outputdir, text=True
    )
    with os.fdopen(fd, 'w') as fp:
        for name, ts in sorted(saved.items()):
            fp.write('%s %s\n' % (name, ' '.join(['%.3f' % (t,) for t in ts])))
    timepath = os.path.join(outputdir, b'.testtimes')
    try:
        os.unlink(timepath)
    except OSError:
        pass
    try:
        os.rename(tmpname, timepath)
    except OSError:
        pass


class TextTestRunner(unittest.TextTestRunner):
    """Custom unittest test runner that uses appropriate settings."""

    def __init__(self, runner, *args, **kwargs):
        super(TextTestRunner, self).__init__(*args, **kwargs)

        self._runner = runner

        self._result = getTestResult()(
            self._runner.options, self.stream, self.descriptions, self.verbosity
        )

    def listtests(self, test):
        test = sorted(test, key=lambda t: t.name)

        self._result.onStart(test)

        for t in test:
            print(t.name)
            self._result.addSuccess(t)

        if self._runner.options.xunit:
            with open(self._runner.options.xunit, "wb") as xuf:
                self._writexunit(self._result, xuf)

        if self._runner.options.json:
            jsonpath = os.path.join(self._runner._outputdir, b'report.json')
            with open(jsonpath, 'w') as fp:
                self._writejson(self._result, fp)

        return self._result

    def run(self, test):
        self._result.onStart(test)
        test(self._result)

        failed = len(self._result.failures)
        skipped = len(self._result.skipped)
        ignored = len(self._result.ignored)

        with iolock:
            self.stream.writeln('')

            if not self._runner.options.noskips:
                for test, msg in sorted(
                    self._result.skipped, key=lambda s: s[0].name
                ):
                    formatted = 'Skipped %s: %s\n' % (test.name, msg)
                    msg = highlightmsg(formatted, self._result.color)
                    self.stream.write(msg)
            for test, msg in sorted(
                self._result.failures, key=lambda f: f[0].name
            ):
                formatted = 'Failed %s: %s\n' % (test.name, msg)
                self.stream.write(highlightmsg(formatted, self._result.color))
            for test, msg in sorted(
                self._result.errors, key=lambda e: e[0].name
            ):
                self.stream.writeln('Errored %s: %s' % (test.name, msg))

            if self._runner.options.xunit:
                with open(self._runner.options.xunit, "wb") as xuf:
                    self._writexunit(self._result, xuf)

            if self._runner.options.json:
                jsonpath = os.path.join(self._runner._outputdir, b'report.json')
                with open(jsonpath, 'w') as fp:
                    self._writejson(self._result, fp)

            self._runner._checkhglib('Tested')

            savetimes(self._runner._outputdir, self._result)

            if failed and self._runner.options.known_good_rev:
                self._bisecttests(t for t, m in self._result.failures)
            self.stream.writeln(
                '# Ran %d tests, %d skipped, %d failed.'
                % (self._result.testsRun, skipped + ignored, failed)
            )
            if failed:
                self.stream.writeln(
                    'python hash seed: %s' % os.environ['PYTHONHASHSEED']
                )
            if self._runner.options.time:
                self.printtimes(self._result.times)

            if self._runner.options.exceptions:
                exceptions = aggregateexceptions(
                    os.path.join(self._runner._outputdir, b'exceptions')
                )

                self.stream.writeln('Exceptions Report:')
                self.stream.writeln(
                    '%d total from %d frames'
                    % (exceptions['total'], len(exceptions['exceptioncounts']))
                )
                combined = exceptions['combined']
                for key in sorted(combined, key=combined.get, reverse=True):
                    frame, line, exc = key
                    totalcount, testcount, leastcount, leasttest = combined[key]

                    self.stream.writeln(
                        '%d (%d tests)\t%s: %s (%s - %d total)'
                        % (
                            totalcount,
                            testcount,
                            frame,
                            exc,
                            leasttest,
                            leastcount,
                        )
                    )

            self.stream.flush()

        return self._result

    def _bisecttests(self, tests):
        bisectcmd = ['hg', 'bisect']
        bisectrepo = self._runner.options.bisect_repo
        if bisectrepo:
            bisectcmd.extend(['-R', os.path.abspath(bisectrepo)])

        def pread(args):
            env = os.environ.copy()
            env['HGPLAIN'] = '1'
            p = subprocess.Popen(
                args, stderr=subprocess.STDOUT, stdout=subprocess.PIPE, env=env
            )
            data = p.stdout.read()
            p.wait()
            return data

        for test in tests:
            pread(bisectcmd + ['--reset']),
            pread(bisectcmd + ['--bad', '.'])
            pread(bisectcmd + ['--good', self._runner.options.known_good_rev])
            # TODO: we probably need to forward more options
            # that alter hg's behavior inside the tests.
            opts = ''
            withhg = self._runner.options.with_hg
            if withhg:
                opts += ' --with-hg=%s ' % shellquote(_strpath(withhg))
            rtc = '%s %s %s %s' % (sysexecutable, sys.argv[0], opts, test)
            data = pread(bisectcmd + ['--command', rtc])
            m = re.search(
                (
                    br'\nThe first (?P<goodbad>bad|good) revision '
                    br'is:\nchangeset: +\d+:(?P<node>[a-f0-9]+)\n.*\n'
                    br'summary: +(?P<summary>[^\n]+)\n'
                ),
                data,
                (re.MULTILINE | re.DOTALL),
            )
            if m is None:
                self.stream.writeln(
                    'Failed to identify failure point for %s' % test
                )
                continue
            dat = m.groupdict()
            verb = 'broken' if dat['goodbad'] == b'bad' else 'fixed'
            self.stream.writeln(
                '%s %s by %s (%s)'
                % (
                    test,
                    verb,
                    dat['node'].decode('ascii'),
                    dat['summary'].decode('utf8', 'ignore'),
                )
            )

    def printtimes(self, times):
        # iolock held by run
        self.stream.writeln('# Producing time report')
        times.sort(key=lambda t: (t[3]))
        cols = '%7.3f %7.3f %7.3f %7.3f %7.3f   %s'
        self.stream.writeln(
            '%-7s %-7s %-7s %-7s %-7s   %s'
            % ('start', 'end', 'cuser', 'csys', 'real', 'Test')
        )
        for tdata in times:
            test = tdata[0]
            cuser, csys, real, start, end = tdata[1:6]
            self.stream.writeln(cols % (start, end, cuser, csys, real, test))

    @staticmethod
    def _writexunit(result, outf):
        # See http://llg.cubic.org/docs/junit/ for a reference.
        timesd = dict((t[0], t[3]) for t in result.times)
        doc = minidom.Document()
        s = doc.createElement('testsuite')
        s.setAttribute('errors', "0")  # TODO
        s.setAttribute('failures', str(len(result.failures)))
        s.setAttribute('name', 'run-tests')
        s.setAttribute(
            'skipped', str(len(result.skipped) + len(result.ignored))
        )
        s.setAttribute('tests', str(result.testsRun))
        doc.appendChild(s)
        for tc in result.successes:
            t = doc.createElement('testcase')
            t.setAttribute('name', tc.name)
            tctime = timesd.get(tc.name)
            if tctime is not None:
                t.setAttribute('time', '%.3f' % tctime)
            s.appendChild(t)
        for tc, err in sorted(result.faildata.items()):
            t = doc.createElement('testcase')
            t.setAttribute('name', tc)
            tctime = timesd.get(tc)
            if tctime is not None:
                t.setAttribute('time', '%.3f' % tctime)
            # createCDATASection expects a unicode or it will
            # convert using default conversion rules, which will
            # fail if string isn't ASCII.
            err = cdatasafe(err).decode('utf-8', 'replace')
            cd = doc.createCDATASection(err)
            # Use 'failure' here instead of 'error' to match errors = 0,
            # failures = len(result.failures) in the testsuite element.
            failelem = doc.createElement('failure')
            failelem.setAttribute('message', 'output changed')
            failelem.setAttribute('type', 'output-mismatch')
            failelem.appendChild(cd)
            t.appendChild(failelem)
            s.appendChild(t)
        for tc, message in result.skipped:
            # According to the schema, 'skipped' has no attributes. So store
            # the skip message as a text node instead.
            t = doc.createElement('testcase')
            t.setAttribute('name', tc.name)
            binmessage = message.encode('utf-8')
            message = cdatasafe(binmessage).decode('utf-8', 'replace')
            cd = doc.createCDATASection(message)
            skipelem = doc.createElement('skipped')
            skipelem.appendChild(cd)
            t.appendChild(skipelem)
            s.appendChild(t)
        outf.write(doc.toprettyxml(indent='  ', encoding='utf-8'))

    @staticmethod
    def _writejson(result, outf):
        timesd = {}
        for tdata in result.times:
            test = tdata[0]
            timesd[test] = tdata[1:]

        outcome = {}
        groups = [
            ('success', ((tc, None) for tc in result.successes)),
            ('failure', result.failures),
            ('skip', result.skipped),
        ]
        for res, testcases in groups:
            for tc, __ in testcases:
                if tc.name in timesd:
                    diff = result.faildata.get(tc.name, b'')
                    try:
                        diff = diff.decode('unicode_escape')
                    except UnicodeDecodeError as e:
                        diff = '%r decoding diff, sorry' % e
                    tres = {
                        'result': res,
                        'time': ('%0.3f' % timesd[tc.name][2]),
                        'cuser': ('%0.3f' % timesd[tc.name][0]),
                        'csys': ('%0.3f' % timesd[tc.name][1]),
                        'start': ('%0.3f' % timesd[tc.name][3]),
                        'end': ('%0.3f' % timesd[tc.name][4]),
                        'diff': diff,
                    }
                else:
                    # blacklisted test
                    tres = {'result': res}

                outcome[tc.name] = tres
        jsonout = json.dumps(
            outcome, sort_keys=True, indent=4, separators=(',', ': ')
        )
        outf.writelines(("testreport =", jsonout))


def sorttests(testdescs, previoustimes, shuffle=False):
    """Do an in-place sort of tests."""
    if shuffle:
        random.shuffle(testdescs)
        return

    if previoustimes:

        def sortkey(f):
            f = f['path']
            if f in previoustimes:
                # Use most recent time as estimate
                return -(previoustimes[f][-1])
            else:
                # Default to a rather arbitrary value of 1 second for new tests
                return -1.0

    else:
        # keywords for slow tests
        slow = {
            b'svn': 10,
            b'cvs': 10,
            b'hghave': 10,
            b'largefiles-update': 10,
            b'run-tests': 10,
            b'corruption': 10,
            b'race': 10,
            b'i18n': 10,
            b'check': 100,
            b'gendoc': 100,
            b'contrib-perf': 200,
            b'merge-combination': 100,
        }
        perf = {}

        def sortkey(f):
            # run largest tests first, as they tend to take the longest
            f = f['path']
            try:
                return perf[f]
            except KeyError:
                try:
                    val = -os.stat(f).st_size
                except OSError as e:
                    if e.errno != errno.ENOENT:
                        raise
                    perf[f] = -1e9  # file does not exist, tell early
                    return -1e9
                for kw, mul in slow.items():
                    if kw in f:
                        val *= mul
                if f.endswith(b'.py'):
                    val /= 10.0
                perf[f] = val / 1000.0
                return perf[f]

    testdescs.sort(key=sortkey)


class TestRunner(object):
    """Holds context for executing tests.

    Tests rely on a lot of state. This object holds it for them.
    """

    # Programs required to run tests.
    REQUIREDTOOLS = [
        b'diff',
        b'grep',
        b'unzip',
        b'gunzip',
        b'bunzip2',
        b'sed',
    ]

    # Maps file extensions to test class.
    TESTTYPES = [
        (b'.py', PythonTest),
        (b'.t', TTest),
    ]

    def __init__(self):
        self.options = None
        self._hgroot = None
        self._testdir = None
        self._outputdir = None
        self._hgtmp = None
        self._installdir = None
        self._bindir = None
        self._tmpbinddir = None
        self._pythondir = None
        self._coveragefile = None
        self._createdfiles = []
        self._hgcommand = None
        self._hgpath = None
        self._portoffset = 0
        self._ports = {}

    def run(self, args, parser=None):
        """Run the test suite."""
        oldmask = os.umask(0o22)
        try:
            parser = parser or getparser()
            options = parseargs(args, parser)
            tests = [_bytespath(a) for a in options.tests]
            if options.test_list is not None:
                for listfile in options.test_list:
                    with open(listfile, 'rb') as f:
                        tests.extend(t for t in f.read().splitlines() if t)
            self.options = options

            self._checktools()
            testdescs = self.findtests(tests)
            if options.profile_runner:
                import statprof

                statprof.start()
            result = self._run(testdescs)
            if options.profile_runner:
                statprof.stop()
                statprof.display()
            return result

        finally:
            os.umask(oldmask)

    def _run(self, testdescs):
        testdir = getcwdb()
        self._testdir = osenvironb[b'TESTDIR'] = getcwdb()
        # assume all tests in same folder for now
        if testdescs:
            pathname = os.path.dirname(testdescs[0]['path'])
            if pathname:
                # TRACKING MOZ
                # osenvironb[b'TESTDIR'] = os.path.join(osenvironb[b'TESTDIR'],
                #                                      pathname)
                pass

        if self.options.outputdir:
            self._outputdir = canonpath(_bytespath(self.options.outputdir))
        else:
            self._outputdir = getcwdb()
            if testdescs and pathname:
                self._outputdir = os.path.join(self._outputdir, pathname)
        previoustimes = {}
        if self.options.order_by_runtime:
            previoustimes = dict(loadtimes(self._outputdir))
        sorttests(testdescs, previoustimes, shuffle=self.options.random)

        if 'PYTHONHASHSEED' not in os.environ:
            # use a random python hash seed all the time
            # we do the randomness ourself to know what seed is used
            os.environ['PYTHONHASHSEED'] = str(random.getrandbits(32))

        if self.options.tmpdir:
            self.options.keep_tmpdir = True
            tmpdir = _bytespath(self.options.tmpdir)
            if os.path.exists(tmpdir):
                # Meaning of tmpdir has changed since 1.3: we used to create
                # HGTMP inside tmpdir; now HGTMP is tmpdir.  So fail if
                # tmpdir already exists.
                print("error: temp dir %r already exists" % tmpdir)
                return 1

            os.makedirs(tmpdir)
        else:
            d = None
            if os.name == 'nt':
                # without this, we get the default temp dir location, but
                # in all lowercase, which causes troubles with paths (issue3490)
                d = osenvironb.get(b'TMP', None)
            tmpdir = tempfile.mkdtemp(b'', b'hgtests.', d)

        self._hgtmp = osenvironb[b'HGTMP'] = os.path.realpath(tmpdir)

        if self.options.with_hg:
            self._installdir = None
            whg = self.options.with_hg
            self._bindir = os.path.dirname(os.path.realpath(whg))
            assert isinstance(self._bindir, bytes)
            self._hgcommand = os.path.basename(whg)
            self._tmpbindir = os.path.join(self._hgtmp, b'install', b'bin')
            os.makedirs(self._tmpbindir)

            normbin = os.path.normpath(os.path.abspath(whg))
            normbin = normbin.replace(os.sep.encode('ascii'), b'/')

            # Other Python scripts in the test harness need to
            # `import mercurial`. If `hg` is a Python script, we assume
            # the Mercurial modules are relative to its path and tell the tests
            # to load Python modules from its directory.
            with open(whg, 'rb') as fh:
                initial = fh.read(1024)

            if re.match(b'#!.*python', initial):
                self._pythondir = self._bindir
            # If it looks like our in-repo Rust binary, use the source root.
            # This is a bit hacky. But rhg is still not supported outside the
            # source directory. So until it is, do the simple thing.
            elif re.search(b'/rust/target/[^/]+/hg', normbin):
                self._pythondir = os.path.dirname(self._testdir)
            # Fall back to the legacy behavior.
            else:
                self._pythondir = self._bindir

        else:
            self._installdir = os.path.join(self._hgtmp, b"install")
            self._bindir = os.path.join(self._installdir, b"bin")
            self._hgcommand = b'hg'
            self._tmpbindir = self._bindir
            self._pythondir = os.path.join(self._installdir, b"lib", b"python")

        # Force the use of hg.exe instead of relying on MSYS to recognize hg is
        # a python script and feed it to python.exe.  Legacy stdio is force
        # enabled by hg.exe, and this is a more realistic way to launch hg
        # anyway.
        if os.name == 'nt' and not self._hgcommand.endswith(b'.exe'):
            self._hgcommand += b'.exe'

        # set CHGHG, then replace "hg" command by "chg"
        chgbindir = self._bindir
        if self.options.chg or self.options.with_chg:
            osenvironb[b'CHGHG'] = os.path.join(self._bindir, self._hgcommand)
        else:
            osenvironb.pop(b'CHGHG', None)  # drop flag for hghave
        if self.options.chg:
            self._hgcommand = b'chg'
        elif self.options.with_chg:
            chgbindir = os.path.dirname(os.path.realpath(self.options.with_chg))
            self._hgcommand = os.path.basename(self.options.with_chg)

        osenvironb[b"BINDIR"] = self._bindir
        osenvironb[b"PYTHON"] = PYTHON

        fileb = _bytespath(__file__)
        runtestdir = os.path.abspath(os.path.dirname(fileb))
        osenvironb[b'RUNTESTDIR'] = runtestdir
        if PYTHON3:
            sepb = _bytespath(os.pathsep)
        else:
            sepb = os.pathsep
        path = [self._bindir, runtestdir] + osenvironb[b"PATH"].split(sepb)
        if os.path.islink(__file__):
            # test helper will likely be at the end of the symlink
            realfile = os.path.realpath(fileb)
            realdir = os.path.abspath(os.path.dirname(realfile))
            path.insert(2, realdir)
        if chgbindir != self._bindir:
            path.insert(1, chgbindir)
        if self._testdir != runtestdir:
            path = [self._testdir] + path
        if self._tmpbindir != self._bindir:
            path = [self._tmpbindir] + path
        osenvironb[b"PATH"] = sepb.join(path)

        # Include TESTDIR in PYTHONPATH so that out-of-tree extensions
        # can run .../tests/run-tests.py test-foo where test-foo
        # adds an extension to HGRC. Also include run-test.py directory to
        # import modules like heredoctest.
        pypath = [self._pythondir, self._testdir, runtestdir]
        # We have to augment PYTHONPATH, rather than simply replacing
        # it, in case external libraries are only available via current
        # PYTHONPATH.  (In particular, the Subversion bindings on OS X
        # are in /opt/subversion.)
        oldpypath = osenvironb.get(IMPL_PATH)
        if oldpypath:
            pypath.append(oldpypath)
        osenvironb[IMPL_PATH] = sepb.join(pypath)

        if self.options.pure:
            os.environ["HGTEST_RUN_TESTS_PURE"] = "--pure"
            os.environ["HGMODULEPOLICY"] = "py"

        if self.options.allow_slow_tests:
            os.environ["HGTEST_SLOW"] = "slow"
        elif 'HGTEST_SLOW' in os.environ:
            del os.environ['HGTEST_SLOW']

        self._coveragefile = os.path.join(self._testdir, b'.coverage')

        if self.options.exceptions:
            exceptionsdir = os.path.join(self._outputdir, b'exceptions')
            try:
                os.makedirs(exceptionsdir)
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise

            # Remove all existing exception reports.
            for f in os.listdir(exceptionsdir):
                os.unlink(os.path.join(exceptionsdir, f))

            osenvironb[b'HGEXCEPTIONSDIR'] = exceptionsdir
            logexceptions = os.path.join(self._testdir, b'logexceptions.py')
            self.options.extra_config_opt.append(
                'extensions.logexceptions=%s' % logexceptions.decode('utf-8')
            )

        vlog("# Using TESTDIR", _strpath(self._testdir))
        vlog("# Using RUNTESTDIR", _strpath(osenvironb[b'RUNTESTDIR']))
        vlog("# Using HGTMP", _strpath(self._hgtmp))
        vlog("# Using PATH", os.environ["PATH"])
        vlog(
            "# Using", _strpath(IMPL_PATH), _strpath(osenvironb[IMPL_PATH]),
        )
        vlog("# Writing to directory", _strpath(self._outputdir))

        try:
            return self._runtests(testdescs) or 0
        finally:
            time.sleep(0.1)
            self._cleanup()

    def findtests(self, args):
        """Finds possible test files from arguments.

        If you wish to inject custom tests into the test harness, this would
        be a good function to monkeypatch or override in a derived class.
        """
        if not args:
            if self.options.changed:
                proc = Popen4(
                    b'hg st --rev "%s" -man0 .'
                    % _bytespath(self.options.changed),
                    None,
                    0,
                )
                stdout, stderr = proc.communicate()
                args = stdout.strip(b'\0').split(b'\0')
            else:
                args = os.listdir(b'.')

        expanded_args = []
        for arg in args:
            if os.path.isdir(arg):
                if not arg.endswith(b'/'):
                    arg += b'/'
                expanded_args.extend([arg + a for a in os.listdir(arg)])
            else:
                expanded_args.append(arg)
        args = expanded_args

        testcasepattern = re.compile(br'([\w-]+\.t|py)(?:#([a-zA-Z0-9_\-.#]+))')
        tests = []
        for t in args:
            case = []

            if not (
                os.path.basename(t).startswith(b'test-')
                and (t.endswith(b'.py') or t.endswith(b'.t'))
            ):

                m = testcasepattern.match(os.path.basename(t))
                if m is not None:
                    t_basename, casestr = m.groups()
                    t = os.path.join(os.path.dirname(t), t_basename)
                    if casestr:
                        case = casestr.split(b'#')
                else:
                    continue

            if t.endswith(b'.t'):
                # .t file may contain multiple test cases
                casedimensions = parsettestcases(t)
                if casedimensions:
                    cases = []

                    def addcases(case, casedimensions):
                        if not casedimensions:
                            cases.append(case)
                        else:
                            for c in casedimensions[0]:
                                addcases(case + [c], casedimensions[1:])

                    addcases([], casedimensions)
                    if case and case in cases:
                        cases = [case]
                    elif case:
                        # Ignore invalid cases
                        cases = []
                    else:
                        pass
                    tests += [{'path': t, 'case': c} for c in sorted(cases)]
                else:
                    tests.append({'path': t})
            else:
                tests.append({'path': t})
        return tests

    def _runtests(self, testdescs):
        def _reloadtest(test, i):
            # convert a test back to its description dict
            desc = {'path': test.path}
            case = getattr(test, '_case', [])
            if case:
                desc['case'] = case
            return self._gettest(desc, i)

        try:
            if self.options.restart:
                orig = list(testdescs)
                while testdescs:
                    desc = testdescs[0]
                    # desc['path'] is a relative path
                    if 'case' in desc:
                        casestr = b'#'.join(desc['case'])
                        errpath = b'%s#%s.err' % (desc['path'], casestr)
                    else:
                        errpath = b'%s.err' % desc['path']
                    errpath = os.path.join(self._outputdir, errpath)
                    if os.path.exists(errpath):
                        break
                    testdescs.pop(0)
                if not testdescs:
                    print("running all tests")
                    testdescs = orig

            tests = [self._gettest(d, i) for i, d in enumerate(testdescs)]
            num_tests = len(tests) * self.options.runs_per_test

            jobs = min(num_tests, self.options.jobs)

            failed = False
            kws = self.options.keywords
            if kws is not None and PYTHON3:
                kws = kws.encode('utf-8')

            suite = TestSuite(
                self._testdir,
                jobs=jobs,
                whitelist=self.options.whitelisted,
                blacklist=self.options.blacklist,
                retest=self.options.retest,
                keywords=kws,
                loop=self.options.loop,
                runs_per_test=self.options.runs_per_test,
                showchannels=self.options.showchannels,
                tests=tests,
                loadtest=_reloadtest,
            )
            verbosity = 1
            if self.options.list_tests:
                verbosity = 0
            elif self.options.verbose:
                verbosity = 2
            runner = TextTestRunner(self, verbosity=verbosity)

            if self.options.list_tests:
                result = runner.listtests(suite)
            else:
                if self._installdir:
                    self._installhg()
                    self._checkhglib("Testing")
                else:
                    self._usecorrectpython()
                if self.options.chg:
                    assert self._installdir
                    self._installchg()

                log(
                    'running %d tests using %d parallel processes'
                    % (num_tests, jobs)
                )

                result = runner.run(suite)

            if result.failures or result.errors:
                failed = True

            result.onEnd()

            if self.options.anycoverage:
                self._outputcoverage()
        except KeyboardInterrupt:
            failed = True
            print("\ninterrupted!")

        if failed:
            return 1

    def _getport(self, count):
        port = self._ports.get(count)  # do we have a cached entry?
        if port is None:
            # TRACKING MOZ - 9 ports
            portneeded = 9
            # above 100 tries we just give up and let test reports failure
            for tries in xrange(100):
                allfree = True
                port = self.options.port + self._portoffset
                for idx in xrange(portneeded):
                    if not checkportisavailable(port + idx):
                        allfree = False
                        break
                self._portoffset += portneeded
                if allfree:
                    break
            self._ports[count] = port
        return port

    def _gettest(self, testdesc, count):
        """Obtain a Test by looking at its filename.

        Returns a Test instance. The Test may not be runnable if it doesn't
        map to a known type.
        """
        path = testdesc['path']
        lctest = path.lower()
        testcls = Test

        for ext, cls in self.TESTTYPES:
            if lctest.endswith(ext):
                testcls = cls
                break

        refpath = os.path.join(getcwdb(), path)
        tmpdir = os.path.join(self._hgtmp, b'child%d' % count)

        # TRACKING MOZ
        errdir = os.path.dirname(refpath)

        # extra keyword parameters. 'case' is used by .t tests
        kwds = dict((k, testdesc[k]) for k in ['case'] if k in testdesc)

        # TRACKING MOZ
        # self._outputdir -> errdir
        t = testcls(
            refpath,
            errdir,
            tmpdir,
            keeptmpdir=self.options.keep_tmpdir,
            debug=self.options.debug,
            first=self.options.first,
            timeout=self.options.timeout,
            startport=self._getport(count),
            extraconfigopts=self.options.extra_config_opt,
            py3warnings=self.options.py3_warnings,
            shell=self.options.shell,
            hgcommand=self._hgcommand,
            usechg=bool(self.options.with_chg or self.options.chg),
            useipv6=useipv6,
            **kwds
        )
        t.should_reload = True
        return t

    def _cleanup(self):
        """Clean up state from this test invocation."""
        if self.options.keep_tmpdir:
            return

        vlog("# Cleaning up HGTMP", _strpath(self._hgtmp))
        shutil.rmtree(self._hgtmp, True)
        for f in self._createdfiles:
            try:
                os.remove(f)
            except OSError:
                pass

    def _usecorrectpython(self):
        # TRACKING MOZ - use the Python already on $PATH
        pass
        #"""Configure the environment to use the appropriate Python in tests."""
        ## Tests must use the same interpreter as us or bad things will happen.
        #pyexename = sys.platform == 'win32' and b'python.exe' or b'python'

        ## os.symlink() is a thing with py3 on Windows, but it requires
        ## Administrator rights.
        #if getattr(os, 'symlink', None) and os.name != 'nt':
        #    vlog(
        #        "# Making python executable in test path a symlink to '%s'"
        #        % sysexecutable
        #    )
        #    mypython = os.path.join(self._tmpbindir, pyexename)
        #    try:
        #        if os.readlink(mypython) == sysexecutable:
        #            return
        #        os.unlink(mypython)
        #    except OSError as err:
        #        if err.errno != errno.ENOENT:
        #            raise
        #    if self._findprogram(pyexename) != sysexecutable:
        #        try:
        #            os.symlink(sysexecutable, mypython)
        #            self._createdfiles.append(mypython)
        #        except OSError as err:
        #            # child processes may race, which is harmless
        #            if err.errno != errno.EEXIST:
        #                raise
        #else:
        #    exedir, exename = os.path.split(sysexecutable)
        #    vlog(
        #        "# Modifying search path to find %s as %s in '%s'"
        #        % (exename, pyexename, exedir)
        #    )
        #    path = os.environ['PATH'].split(os.pathsep)
        #    while exedir in path:
        #        path.remove(exedir)
        #    os.environ['PATH'] = os.pathsep.join([exedir] + path)
        #    if not self._findprogram(pyexename):
        #        print("WARNING: Cannot find %s in search path" % pyexename)

    def _installhg(self):
        """Install hg into the test environment.

        This will also configure hg with the appropriate testing settings.
        """
        vlog("# Performing temporary installation of HG")
        installerrs = os.path.join(self._hgtmp, b"install.err")
        compiler = ''
        if self.options.compiler:
            compiler = '--compiler ' + self.options.compiler
        if self.options.pure:
            pure = b"--pure"
        else:
            pure = b""

        # Run installer in hg root
        script = os.path.realpath(sys.argv[0])
        exe = sysexecutable
        if PYTHON3:
            compiler = _bytespath(compiler)
            script = _bytespath(script)
            exe = _bytespath(exe)
        hgroot = os.path.dirname(os.path.dirname(script))
        self._hgroot = hgroot
        os.chdir(hgroot)
        nohome = b'--home=""'
        if os.name == 'nt':
            # The --home="" trick works only on OS where os.sep == '/'
            # because of a distutils convert_path() fast-path. Avoid it at
            # least on Windows for now, deal with .pydistutils.cfg bugs
            # when they happen.
            nohome = b''
        cmd = (
            b'"%(exe)s" setup.py %(pure)s clean --all'
            b' build %(compiler)s --build-base="%(base)s"'
            b' install --force --prefix="%(prefix)s"'
            b' --install-lib="%(libdir)s"'
            b' --install-scripts="%(bindir)s" %(nohome)s >%(logfile)s 2>&1'
            % {
                b'exe': exe,
                b'pure': pure,
                b'compiler': compiler,
                b'base': os.path.join(self._hgtmp, b"build"),
                b'prefix': self._installdir,
                b'libdir': self._pythondir,
                b'bindir': self._bindir,
                b'nohome': nohome,
                b'logfile': installerrs,
            }
        )

        # setuptools requires install directories to exist.
        def makedirs(p):
            try:
                os.makedirs(p)
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise

        makedirs(self._pythondir)
        makedirs(self._bindir)

        vlog("# Running", cmd.decode("utf-8"))
        if subprocess.call(_strpath(cmd), shell=True) == 0:
            if not self.options.verbose:
                try:
                    os.remove(installerrs)
                except OSError as e:
                    if e.errno != errno.ENOENT:
                        raise
        else:
            with open(installerrs, 'rb') as f:
                for line in f:
                    if PYTHON3:
                        sys.stdout.buffer.write(line)
                    else:
                        sys.stdout.write(line)
            sys.exit(1)
        os.chdir(self._testdir)

        self._usecorrectpython()

        if self.options.py3_warnings and not self.options.anycoverage:
            vlog("# Updating hg command to enable Py3k Warnings switch")
            with open(os.path.join(self._bindir, 'hg'), 'rb') as f:
                lines = [line.rstrip() for line in f]
                lines[0] += ' -3'
            with open(os.path.join(self._bindir, 'hg'), 'wb') as f:
                for line in lines:
                    f.write(line + '\n')

        hgbat = os.path.join(self._bindir, b'hg.bat')
        if os.path.isfile(hgbat):
            # hg.bat expects to be put in bin/scripts while run-tests.py
            # installation layout put it in bin/ directly. Fix it
            with open(hgbat, 'rb') as f:
                data = f.read()
            if br'"%~dp0..\python" "%~dp0hg" %*' in data:
                data = data.replace(
                    br'"%~dp0..\python" "%~dp0hg" %*',
                    b'"%~dp0python" "%~dp0hg" %*',
                )
                with open(hgbat, 'wb') as f:
                    f.write(data)
            else:
                print('WARNING: cannot fix hg.bat reference to python.exe')

        if self.options.anycoverage:
            custom = os.path.join(
                osenvironb[b'RUNTESTDIR'], b'sitecustomize.py'
            )
            target = os.path.join(self._pythondir, b'sitecustomize.py')
            vlog('# Installing coverage trigger to %s' % target)
            shutil.copyfile(custom, target)
            rc = os.path.join(self._testdir, b'.coveragerc')
            vlog('# Installing coverage rc to %s' % rc)
            osenvironb[b'COVERAGE_PROCESS_START'] = rc
            covdir = os.path.join(self._installdir, b'..', b'coverage')
            try:
                os.mkdir(covdir)
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise

            osenvironb[b'COVERAGE_DIR'] = covdir

    def _checkhglib(self, verb):
        """Ensure that the 'mercurial' package imported by python is
        the one we expect it to be.  If not, print a warning to stderr."""
        if (self._bindir == self._pythondir) and (
            self._bindir != self._tmpbindir
        ):
            # The pythondir has been inferred from --with-hg flag.
            # We cannot expect anything sensible here.
            return
        expecthg = os.path.join(self._pythondir, b'mercurial')
        actualhg = self._gethgpath()
        if os.path.abspath(actualhg) != os.path.abspath(expecthg):
            sys.stderr.write(
                'warning: %s with unexpected mercurial lib: %s\n'
                '         (expected %s)\n' % (verb, actualhg, expecthg)
            )

    def _gethgpath(self):
        """Return the path to the mercurial package that is actually found by
        the current Python interpreter."""
        if self._hgpath is not None:
            return self._hgpath

        cmd = b'"%s" -c "import mercurial; print (mercurial.__path__[0])"'
        cmd = cmd % PYTHON
        if PYTHON3:
            cmd = _strpath(cmd)

        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
        out, err = p.communicate()

        self._hgpath = out.strip()

        return self._hgpath

    def _installchg(self):
        """Install chg into the test environment"""
        vlog('# Performing temporary installation of CHG')
        assert os.path.dirname(self._bindir) == self._installdir
        assert self._hgroot, 'must be called after _installhg()'
        cmd = b'"%(make)s" clean install PREFIX="%(prefix)s"' % {
            b'make': b'make',  # TODO: switch by option or environment?
            b'prefix': self._installdir,
        }
        cwd = os.path.join(self._hgroot, b'contrib', b'chg')
        vlog("# Running", cmd)
        proc = subprocess.Popen(
            cmd,
            shell=True,
            cwd=cwd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        out, _err = proc.communicate()
        if proc.returncode != 0:
            if PYTHON3:
                sys.stdout.buffer.write(out)
            else:
                sys.stdout.write(out)
            sys.exit(1)

    def _outputcoverage(self):
        """Produce code coverage output."""
        import coverage

        coverage = coverage.coverage

        vlog('# Producing coverage report')
        # chdir is the easiest way to get short, relative paths in the
        # output.
        os.chdir(self._hgroot)
        covdir = os.path.join(_strpath(self._installdir), '..', 'coverage')
        cov = coverage(data_file=os.path.join(covdir, 'cov'))

        # Map install directory paths back to source directory.
        cov.config.paths['srcdir'] = ['.', _strpath(self._pythondir)]

        cov.combine()

        omit = [
            _strpath(os.path.join(x, b'*'))
            for x in [self._bindir, self._testdir]
        ]
        cov.report(ignore_errors=True, omit=omit)

        if self.options.htmlcov:
            htmldir = os.path.join(_strpath(self._outputdir), 'htmlcov')
            cov.html_report(directory=htmldir, omit=omit)
        if self.options.annotate:
            adir = os.path.join(_strpath(self._outputdir), 'annotated')
            if not os.path.isdir(adir):
                os.mkdir(adir)
            cov.annotate(directory=adir, omit=omit)

    def _findprogram(self, program):
        """Search PATH for a executable program"""
        dpb = _bytespath(os.defpath)
        sepb = _bytespath(os.pathsep)
        for p in osenvironb.get(b'PATH', dpb).split(sepb):
            name = os.path.join(p, program)
            if os.name == 'nt' or os.access(name, os.X_OK):
                return name
        return None

    def _checktools(self):
        """Ensure tools required to run tests are present."""
        for p in self.REQUIREDTOOLS:
            if os.name == 'nt' and not p.endswith(b'.exe'):
                p += b'.exe'
            found = self._findprogram(p)
            p = p.decode("utf-8")
            if found:
                vlog("# Found prerequisite", p, "at", _strpath(found))
            else:
                print("WARNING: Did not find prerequisite tool: %s " % p)


def aggregateexceptions(path):
    exceptioncounts = collections.Counter()
    testsbyfailure = collections.defaultdict(set)
    failuresbytest = collections.defaultdict(set)

    for f in os.listdir(path):
        with open(os.path.join(path, f), 'rb') as fh:
            data = fh.read().split(b'\0')
            if len(data) != 5:
                continue

            exc, mainframe, hgframe, hgline, testname = data
            exc = exc.decode('utf-8')
            mainframe = mainframe.decode('utf-8')
            hgframe = hgframe.decode('utf-8')
            hgline = hgline.decode('utf-8')
            testname = testname.decode('utf-8')

            key = (hgframe, hgline, exc)
            exceptioncounts[key] += 1
            testsbyfailure[key].add(testname)
            failuresbytest[testname].add(key)

    # Find test having fewest failures for each failure.
    leastfailing = {}
    for key, tests in testsbyfailure.items():
        fewesttest = None
        fewestcount = 99999999
        for test in sorted(tests):
            if len(failuresbytest[test]) < fewestcount:
                fewesttest = test
                fewestcount = len(failuresbytest[test])

        leastfailing[key] = (fewestcount, fewesttest)

    # Create a combined counter so we can sort by total occurrences and
    # impacted tests.
    combined = {}
    for key in exceptioncounts:
        combined[key] = (
            exceptioncounts[key],
            len(testsbyfailure[key]),
            leastfailing[key][0],
            leastfailing[key][1],
        )

    return {
        'exceptioncounts': exceptioncounts,
        'total': sum(exceptioncounts.values()),
        'combined': combined,
        'leastfailing': leastfailing,
        'byfailure': testsbyfailure,
        'bytest': failuresbytest,
    }


if __name__ == '__main__':
    runner = TestRunner()

    try:
        import msvcrt

        msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
        msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
        msvcrt.setmode(sys.stderr.fileno(), os.O_BINARY)
    except ImportError:
        pass

    sys.exit(runner.run(sys.argv[1:]))
