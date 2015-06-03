# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

"""Perform clones by first downloading static bundles.

Cloning large repositories can be resource intensive on the server because
Mercurial needs to work to serve that data.

This extension relieves some of that load by changing clone to first obtain
a pre-generated bundle file. Since the bundle file is pre-generated and
serving static files should not be as resource intensive as producing a
bundle at clone time, this results in a net reduction of server work.

Client Use
==========

To enable cloning from bundles, simply enable this extension on the client.

If the server supports bundle clones and a bundle is available, it will be
used. If not, there is no change in behavior.

The ``bundleclone.pullmanifest`` boolean config flag can be set to enable
pulling the bundleclone manifest from the server during clone and pull
operations. It is not enabled by default.

Server Use
==========

During clone, the contents of .hg/bundleclone.manifest are transferred to the
client and parsed for suitable bundles.

Each line in this file defines an available bundle. Lines have the format:

    <URL> [<key>=<value]

That is, a URL followed by extra metadata describing it. Metadata keys and
values should be URL encoded.

This metadata is optional. It is up to server operators to populate this
metadata. See below for use cases.

The server operator is responsible for generating the bundle manifest file.

While the bundle manifest can consist of multiple lines, the client will
currently only consult the first line unless attribute preferences are
defined. See below.

Using Stream Bundles
--------------------

Mercurial has an alternative clone mode accessed via
``hg clone --uncompressed`` that effectively streams raw files across the wire.
This is conceptually similar to streaming a tar file. Assuming the network is
not limiting throughput, this clone mode is significantly faster because it
consumes much less CPU (the client is effectively writing files from a buffer).
The downside to this approach is total size of transferred data is slightly
larger. But in environments with plentiful bandwidth and high throughput, this
trade-off is often worth it.

To produce stream bundles (which aren't technically Mercurial bundles), you'll
need to run the following command:

    $ hg streambundle <output file>

Manifest entries for stream bundles *must* contain a ``stream`` attribute
whose value contains a comma delimited list of requirements. This content will
be printed by the ``streambundle`` command.

Generating the Bundle Manifest
------------------------------

Before you generate the bundle manifest, you must first generate a bundle.
This can be done with the ``hg bundle`` command.

A bundle with gzip compression will behave most similarly to what Mercurial
does by default at clone time. bzip2 bundles will be smaller (they will
transfer faster) but will require more CPU to generate and apply. For large
repos, this could significantly increase clone time.

A recommended bundle generation command that gets you close to Mercurial
defaults is:

    $ hg bundle --all --type gzip bundle.hg

You have the choice of using a static filename / URL with an ever-changing
file/bundle underneath or using separate files/URLs backed by constant
content. The former keeps your ``bundle.manifest`` files static. The latter
has significant advantages for HTTP, including more reliable resume support
and better support for caching. With idempotent HTTP GETs, you can set
aggressive Cache-Control headers to enable downstream caching. The choice
is yours.

If you want to produce separate files/URLs for each bundle, we recommend
including the tip changeset as part of the filename. For example:

    $ hg bundle --all --type gzip `hg log --template '{node|short}' -r tip`.hg

From there, make the bundle file available where the client can access it and
place that URL in the ``.hg/bundleclone.manifest`` file. e.g.:

    https://example.com/bundles/d31fe614fa1e.hg

Using Attributes to Prefer Bundles
==================================

Manifest may define attributes next to each entry. Attributes can be used by
clients to *prefer* one bundle over another. For example, a client on a slow
internet connection may wish to prefer bzip2 bundles because they are smaller.
Or, a server operator may wish to hosts bundles in S3 in multiple EC2 regions
and have clients fetch from the closest EC2 region. Assigning the compression
format and/or EC2 region to an attribute could allow clients to fetch the best
bundle for them.

As described above, attributes simply need to be set in the bundle manifest
file on the server.

To use these attributes, clients will need to define the
``bundleclone.prefers`` config option. This option is a list of ``key=value``
pairs that define attribute names and their preferred values. e.g.::

    [bundleclone]
    prefers = ec2region=us-west-1 ec2region=us-east-1 compression=gzip

The client sorts the server-provided manifest according to preferences defined
in ``bundleclone.prefers``. The sorting method is very simple: an entry is
preferred over another the earlier a match in the attributes list occurs.

In the above example, the client will select the first available from the
following:

1. a gzip2 bundle in the us-west-1 region
2. a gzip2 bundle in the us-east-1 region
3. any available bundle in us-west-1
4. any available bundle in us-east-1
5. any available gzip bundle in any region
6. any available bundle

Failure Behavior
================

By default, clients will abort if an error occurred while fetching a bundle.
The behavior can be changed to fall back to cloning via regular means by
setting the ``bundleclone.fallbackonerror`` boolean config option.

The reason clients don't fall back to a regular clone on failure is because
this may overwhelm the Mercurial server. Many reasons for deploying clone from
bundle support is to help reduce server load. A server may expect that most
clones are serviced by bundles and thus effectively free for the server to
handle. If bundles started failing all of a sudden, the server could
potentially be flooded by tons of new clone requests, drastically increasing
its load and possibly overwhelming it. Disallowing fallback on failure is a
safeguard to prevent this from happening.

"""

import time
import urllib
import urllib2

import mercurial.changegroup as changegroup
import mercurial.cmdutil as cmdutil
import mercurial.demandimport as demandimport
import mercurial.error as error
import mercurial.extensions as extensions
from mercurial.i18n import _
import mercurial.store as store
import mercurial.url as hgurl
import mercurial.util as util
import mercurial.wireproto as wireproto

demandimport.disable()
try:
    from mercurial import exchange
except ImportError:
    exchange = None
demandimport.enable()

testedwith = '2.5 2.6 2.7 2.8 2.9 3.0 3.1 3.2 3.3 3.4'
buglink = 'https://bugzilla.mozilla.org/enter_bug.cgi?product=Developer%20Services&component=Mercurial%3A%20bundleclone'

cmdtable = {}
command = cmdutil.command(cmdtable)

origcapabilities = wireproto.capabilities


def generatestreamclone(repo):
    """Emit content for a streaming clone.

    This is a generator of raw chunks that constitute a streaming clone.

    This code is copied from Mercurial. Until Mercurial 3.5, this code was
    a closure in wireproto.py and not consumeable by extensions.
    """
    entries = []
    total_bytes = 0
    # Get consistent snapshot of repo, lock during scan.
    lock = repo.lock()
    try:
        repo.ui.debug('scanning\n')
        for name, ename, size in repo.store.walk():
            if size:
                entries.append((name, size))
                total_bytes += size
    finally:
            lock.release()

    repo.ui.debug('%d files, %d bytes to transfer\n' %
                  (len(entries), total_bytes))
    yield '%d %d\n' % (len(entries), total_bytes)

    sopener = repo.svfs
    oldaudit = sopener.mustaudit
    debugflag = repo.ui.debugflag
    sopener.mustaudit = False

    try:
        for name, size in entries:
            if debugflag:
                repo.ui.debug('sending %s (%d bytes)\n' % (name, size))
            # partially encode name over the wire for backwards compat
            yield '%s\0%d\n' % (store.encodedir(name), size)
            if size <= 65536:
                fp = sopener(name)
                try:
                    data = fp.read(size)
                finally:
                    fp.close()
                yield data
            else:
                for chunk in util.filechunkiter(sopener(name), limit=size):
                    yield chunk
    finally:
        sopener.mustaudit = oldaudit


def consumestreamclone(repo, fp):
    """Apply the contents from a streaming clone file.

    This code is copied from Mercurial. Until Mercurial 3.5, this code was
    a closure in wireproto.py and not consumeable by extensions.
    """
    lock = repo.lock()
    try:
        repo.ui.status(_('streaming all changes\n'))
        l = fp.readline()
        try:
            total_files, total_bytes = map(int, l.split(' ', 1))
        except (ValueError, TypeError):
            raise error.ResponseError(
                _('unexpected response from remote server:'), l)
        repo.ui.status(_('%d files to transfer, %s of data\n') %
                       (total_files, util.bytecount(total_bytes)))
        handled_bytes = 0
        repo.ui.progress(_('clone'), 0, total=total_bytes)
        start = time.time()

        tr = repo.transaction(_('clone'))
        try:
            for i in xrange(total_files):
                # XXX doesn't support '\n' or '\r' in filenames
                l = fp.readline()
                try:
                    name, size = l.split('\0', 1)
                    size = int(size)
                except (ValueError, TypeError):
                    raise error.ResponseError(
                        _('unexpected response from remote server:'), l)
                if repo.ui.debugflag:
                    repo.ui.debug('adding %s (%s)\n' %
                                  (name, util.bytecount(size)))
                # for backwards compat, name was partially encoded
                ofp = repo.svfs(store.decodedir(name), 'w')
                for chunk in util.filechunkiter(fp, limit=size):
                    handled_bytes += len(chunk)
                    repo.ui.progress(_('clone'), handled_bytes,
                                     total=total_bytes)
                    ofp.write(chunk)
                ofp.close()
            tr.close()
        finally:
            tr.release()

        # Writing straight to files circumvented the inmemory caches
        repo.invalidate()

        elapsed = time.time() - start
        if elapsed <= 0:
            elapsed = 0.001
        repo.ui.progress(_('clone'), None)
        repo.ui.status(_('transferred %s in %.1f seconds (%s/sec)\n') %
                       (util.bytecount(total_bytes), elapsed,
                        util.bytecount(total_bytes / elapsed)))
    finally:
        lock.release()


def applystreamclone(repo, remotereqs, fp):
    """Apply stream clone data to a repository.

    This code is mostly copied from mercurial.repository.stream_in. We needed
    to copy the code because the original code was tightly coupled to the wire
    protocol and not suitable for reuse. Code for dealing with the branch map
    has been removed, as it isn't relevant to our needs.
    """
    lock = repo.lock()
    try:
        consumestreamclone(repo, fp)

        # new requirements = old non-format requirements +
        #                    new format-related remote requirements
        # requirements from the streamed-in repository
        repo.requirements = list(remotereqs | (
                set(repo.requirements) - repo.supportedformats))
        if hasattr(repo, '_applyopenerreqs'):
            repo._applyopenerreqs()
        else:
            repo._applyrequirements(repo.requirements)
        repo._writerequirements()
        repo.invalidate()
    finally:
        lock.release()


def capabilities(*args, **kwargs):
    return origcapabilities(*args, **kwargs) + ' bundles'

def bundles(repo, proto):
    """Server command for returning info for available bundles.

    Clients will parse this response and determine what bundle to fetch.
    """
    return repo.opener.tryread('bundleclone.manifest')

def pull(orig, repo, remote, *args, **kwargs):
    res = orig(repo, remote, *args, **kwargs)

    if remote.capable('bundles') and \
            repo.ui.configbool('bundleclone', 'pullmanifest', False):

        lock = repo.lock()
        repo.ui.status(_('pulling bundleclone manifest\n'))
        manifest = remote._call('bundles')
        try:
            repo.opener.write('bundleclone.manifest', manifest)
        finally:
            lock.release()

    return res


@command('streambundle', [], _('hg streambundle path'))
def streambundle(ui, repo, path):
    """Generate a stream bundle file for a repository."""

    requires = set(repo.requirements) & repo.supportedformats
    if requires - set(['revlogv1']):
        raise util.Abort(_('cannot generate stream bundle for this repo '
            'because of requirement: %s') % (' '.join(requires)))

    ui.status(_('writing %s\n') % path)
    with open(path, 'w') as fh:
        for chunk in generatestreamclone(repo):
            fh.write(chunk)

    ui.write(_('stream bundle file written successully.\n'))
    ui.write(_('include the following in its manifest entry:\n'))
    ui.write('stream=%s\n' % ','.join(requires))

def extsetup(ui):
    # exchange isn't available on older Mercurial. Wrapped pull pulls down
    # the bundle manifest. We don't need this feature on all clients running
    # <3.3, so we silently ignore the failure.
    if exchange:
        extensions.wrapfunction(exchange, 'pull', pull)

    wireproto.capabilities = capabilities
    wireproto.commands['capabilities'] = (capabilities, '')
    wireproto.commands['bundles'] = (bundles, '')

def reposetup(ui, repo):
    if not repo.local():
        return

    class bundleclonerepo(repo.__class__):
        def clone(self, remote, heads=[], stream=False):
            supported = True
            if not remote.capable('bundles'):
                supported = False
                self.ui.debug(_('bundle clone not supported\n'))
            elif heads:
                supported = False
                self.ui.debug(_('cannot perform bundle clone if heads requested\n'))
            elif stream:
                supported = False
                self.ui.debug(_('ignoring bundle clone because stream was '
                                'requested\n'))

            if not supported:
                return super(bundleclonerepo, self).clone(remote, heads=heads,
                        stream=stream)

            result = remote._call('bundles')

            if not result:
                self.ui.note(_('no bundles available; using normal clone\n'))
                return super(bundleclonerepo, self).clone(remote, heads=heads,
                        stream=stream)

            entries = []

            for line in result.splitlines():
                fields = line.split()
                url = fields[0]
                attrs = {}
                for rawattr in fields[1:]:
                    key, value = rawattr.split('=', 1)
                    attrs[urllib.unquote(key)] = urllib.unquote(value)

                entries.append((url, attrs))

            # The configuration is allowed to define lists of preferred
            # attributes and values. If this is present, sort results according
            # to that preference. Otherwise, use manifest order and select the
            # first entry.
            prefers = self.ui.configlist('bundleclone', 'prefers', default=[])
            if prefers:
                prefers = [p.split('=', 1) for p in prefers]

                def compareentry(a, b):
                    aattrs = a[1]
                    battrs = b[1]

                    # Itereate over local preferences.
                    for pkey, pvalue in prefers:
                        avalue = aattrs.get(pkey)
                        bvalue = battrs.get(pkey)

                        # Special case for b is missing attribute and a matches
                        # exactly.
                        if avalue is not None and bvalue is None and avalue == pvalue:
                            return -1

                        # Special case for a missing attribute and b matches
                        # exactly.
                        if bvalue is not None and avalue is None and bvalue == pvalue:
                            return 1

                        # We can't compare unless the attribute is defined on
                        # both entries.
                        if avalue is None or bvalue is None:
                            continue

                        # Same values should fall back to next attribute.
                        if avalue == bvalue:
                            continue

                        # Exact matches come first.
                        if avalue == pvalue:
                            return -1
                        if bvalue == pvalue:
                            return 1

                        # Fall back to next attribute.
                        continue

                    # Entries could not be sorted based on attributes. This
                    # says they are equal, which will fall back to index order,
                    # which is what we want.
                    return 0

                entries = sorted(entries, cmp=compareentry)

            url, attrs = entries[0]

            if not url:
                self.ui.note(_('invalid bundle manifest; using normal clone\n'))
                return super(bundleclonerepo, self).clone(remote, heads=heads,
                        stream=stream)

            self.ui.status(_('downloading bundle %s\n' % url))

            try:
                fh = hgurl.open(self.ui, url)
                # Stream clone data is not changegroup data. Handle it
                # specially.
                if 'stream' in attrs:
                    reqs = set(attrs['stream'].split(','))
                    applystreamclone(self, reqs, fh)
                else:
                    if exchange:
                        cg = exchange.readbundle(self.ui, fh, 'stream')
                    else:
                        cg = changegroup.readbundle(fh, 'stream')

                    if hasattr(changegroup, 'addchangegroup'):
                        changegroup.addchangegroup(self, cg, 'bundleclone', url)
                    else:
                        self.addchangegroup(cg, 'bundleclone', url)

                self.ui.status(_('finishing applying bundle; pulling\n'))
                # Maintain compatibility with Mercurial 2.x.
                if exchange:
                    return exchange.pull(self, remote, heads=heads)
                else:
                    return self.pull(remote, heads=heads)

            except (urllib2.HTTPError, urllib2.URLError) as e:
                if isinstance(e, urllib2.HTTPError):
                    msg = _('HTTP error fetching bundle: %s') % str(e)
                else:
                    msg = _('error fetching bundle: %s') % e.reason

                # Don't fall back to regular clone unless explicitly told to.
                if not self.ui.configbool('bundleclone', 'fallbackonerror', False):
                    raise util.Abort(msg, hint=_('consider contacting the '
                        'server operator if this error persists'))

                self.ui.warn(msg + '\n')
                self.ui.warn(_('falling back to normal clone\n'))

                return super(bundleclonerepo, self).clone(remote, heads=heads,
                        stream=stream)

    repo.__class__ = bundleclonerepo
