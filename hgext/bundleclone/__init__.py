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

SNI
===

Python < 2.7.9 does not support SNI, a TLS extension that allows multiple
SSL certificates to be installed on the same IP. Hosting services often
use SNI to enable multiple services to exist on the same IP.

In addition, Mercurial < 3.3 did not support using the modern SSL capabilities
exposed by modern Python versions. Therefore SNI does not work on Mercurial <
3.3.

The ``requiresni`` manifest attribute can be defined on the server to
indicate whether an entry requires SNI. If it is ``true`` and the client
doesn't support SNI, the entry is automatically discarded. For this reason,
server operators may want to ensure that there is a non-SNI entry in the
manifest to ensure all clients can fetch the bundles.
"""

import struct
import sys
import time
import urllib
import urllib2

import mercurial.branchmap as branchmap
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

testedwith = '2.5 2.6 2.7 2.8 2.9 3.0 3.1 3.2 3.3 3.4 3.5 3.6'
buglink = 'https://bugzilla.mozilla.org/enter_bug.cgi?product=Developer%20Services&component=Mercurial%3A%20bundleclone'

cmdtable = {}
command = cmdutil.command(cmdtable)

origcapabilities = wireproto.capabilities


# BEGIN COPY OF CONTENT FROM mercurial/streamclone.py.
# We copy parts of upstream streamclone.py into this file so we have a single
# API to deal with. Otherwise, we are calling functions from up to 3 different
# locations depending on the Mercurial version.

def canperformstreamclone(pullop, bailifbundle2supported=False):
    """Whether it is possible to perform a streaming clone as part of pull.

    ``bailifbundle2supported`` will cause the function to return False if
    bundle2 stream clones are supported. It should only be called by the
    legacy stream clone code path.

    Returns a tuple of (supported, requirements). ``supported`` is True if
    streaming clone is supported and False otherwise. ``requirements`` is
    a set of repo requirements from the remote, or ``None`` if stream clone
    isn't supported.
    """
    repo = pullop.repo
    remote = pullop.remote

    bundle2supported = False
    if pullop.canusebundle2:
        if 'v1' in pullop.remotebundle2caps.get('stream', []):
            bundle2supported = True
        # else
            # Server doesn't support bundle2 stream clone or doesn't support
            # the versions we support. Fall back and possibly allow legacy.

    # Ensures legacy code path uses available bundle2.
    if bailifbundle2supported and bundle2supported:
        return False, None
    # Ensures bundle2 doesn't try to do a stream clone if it isn't supported.
    #elif not bailifbundle2supported and not bundle2supported:
    #    return False, None

    # Streaming clone only works on empty repositories.
    if len(repo):
        return False, None

    # Streaming clone only works if all data is being requested.
    if pullop.heads:
        return False, None

    streamrequested = pullop.streamclonerequested

    # If we don't have a preference, let the server decide for us. This
    # likely only comes into play in LANs.
    if streamrequested is None:
        # The server can advertise whether to prefer streaming clone.
        streamrequested = remote.capable('stream-preferred')

    if not streamrequested:
        return False, None

    # In order for stream clone to work, the client has to support all the
    # requirements advertised by the server.
    #
    # The server advertises its requirements via the "stream" and "streamreqs"
    # capability. "stream" (a value-less capability) is advertised if and only
    # if the only requirement is "revlogv1." Else, the "streamreqs" capability
    # is advertised and contains a comma-delimited list of requirements.
    requirements = set()
    if remote.capable('stream'):
        requirements.add('revlogv1')
    else:
        streamreqs = remote.capable('streamreqs')
        # This is weird and shouldn't happen with modern servers.
        if not streamreqs:
            return False, None

        streamreqs = set(streamreqs.split(','))
        # Server requires something we don't support. Bail.
        if streamreqs - repo.supportedformats:
            return False, None
        requirements = streamreqs

    return True, requirements

def maybeperformlegacystreamclone(pullop):
    """Possibly perform a legacy stream clone operation.

    Legacy stream clones are performed as part of pull but before all other
    operations.

    A legacy stream clone will not be performed if a bundle2 stream clone is
    supported.
    """
    supported, requirements = canperformstreamclone(pullop)

    if not supported:
        return

    repo = pullop.repo
    remote = pullop.remote

    # Save remote branchmap. We will use it later to speed up branchcache
    # creation.
    rbranchmap = None
    if remote.capable('branchmap'):
        rbranchmap = remote.branchmap()

    repo.ui.status(_('streaming all changes\n'))

    fp = remote.stream_out()
    l = fp.readline()
    try:
        resp = int(l)
    except ValueError:
        raise error.ResponseError(
            _('unexpected response from remote server:'), l)
    if resp == 1:
        raise error.Abort(_('operation forbidden by server'))
    elif resp == 2:
        raise error.Abort(_('locking the remote repository failed'))
    elif resp != 0:
        raise error.Abort(_('the server sent an unknown error code'))

    l = fp.readline()
    try:
        filecount, bytecount = map(int, l.split(' ', 1))
    except (ValueError, TypeError):
        raise error.ResponseError(
            _('unexpected response from remote server:'), l)

    lock = repo.lock()
    try:
        consumev1(repo, fp, filecount, bytecount)

        # new requirements = old non-format requirements +
        #                    new format-related remote requirements
        # requirements from the streamed-in repository
        repo.requirements = requirements | (
                repo.requirements - repo.supportedformats)
        repo._applyopenerreqs()
        repo._writerequirements()

        if rbranchmap:
            branchmap.replacecache(repo, rbranchmap)

        repo.invalidate()
    finally:
        lock.release()

def allowservergeneration(ui):
    """Whether streaming clones are allowed from the server."""
    return ui.configbool('server', 'uncompressed', True, untrusted=True)

# This is it's own function so extensions can override it.
def _walkstreamfiles(repo):
    return repo.store.walk()

def generatev1(repo):
    """Emit content for version 1 of a streaming clone.

    This returns a 3-tuple of (file count, byte size, data iterator).

    The data iterator consists of N entries for each file being transferred.
    Each file entry starts as a line with the file name and integer size
    delimited by a null byte.

    The raw file data follows. Following the raw file data is the next file
    entry, or EOF.

    When used on the wire protocol, an additional line indicating protocol
    success will be prepended to the stream. This function is not responsible
    for adding it.

    This function will obtain a repository lock to ensure a consistent view of
    the store is captured. It therefore may raise LockError.
    """
    entries = []
    total_bytes = 0
    # Get consistent snapshot of repo, lock during scan.
    lock = repo.lock()
    try:
        repo.ui.debug('scanning\n')
        for name, ename, size in _walkstreamfiles(repo):
            if size:
                entries.append((name, size))
                total_bytes += size
    finally:
            lock.release()

    repo.ui.debug('%d files, %d bytes to transfer\n' %
                  (len(entries), total_bytes))

    svfs = repo.svfs
    oldaudit = svfs.mustaudit
    debugflag = repo.ui.debugflag
    svfs.mustaudit = False

    def emitrevlogdata():
        try:
            for name, size in entries:
                if debugflag:
                    repo.ui.debug('sending %s (%d bytes)\n' % (name, size))
                # partially encode name over the wire for backwards compat
                yield '%s\0%d\n' % (store.encodedir(name), size)
                if size <= 65536:
                    fp = svfs(name)
                    try:
                        data = fp.read(size)
                    finally:
                        fp.close()
                    yield data
                else:
                    for chunk in util.filechunkiter(svfs(name), limit=size):
                        yield chunk
        finally:
            svfs.mustaudit = oldaudit

    return len(entries), total_bytes, emitrevlogdata()

def generatev1wireproto(repo):
    """Emit content for version 1 of streaming clone suitable for the wire.

    This is the data output from ``generatev1()`` with a header line
    indicating file count and byte size.
    """
    filecount, bytecount, it = generatev1(repo)
    yield '%d %d\n' % (filecount, bytecount)
    for chunk in it:
        yield chunk

def generatebundlev1(repo, compression='UN'):
    """Emit content for version 1 of a stream clone bundle.

    The first 4 bytes of the output ("HGS1") denote this as stream clone
    bundle version 1.

    The next 2 bytes indicate the compression type. Only "UN" is currently
    supported.

    The next 16 bytes are two 64-bit big endian unsigned integers indicating
    file count and byte count, respectively.

    The next 2 bytes is a 16-bit big endian unsigned short declaring the length
    of the requirements string, including a trailing \0. The following N bytes
    are the requirements string, which is ASCII containing a comma-delimited
    list of repo requirements that are needed to support the data.

    The remaining content is the output of ``generatev1()`` (which may be
    compressed in the future).

    Returns a tuple of (requirements, data generator).
    """
    if compression != 'UN':
        raise ValueError('we do not support the compression argument yet')

    requirements = repo.requirements & repo.supportedformats
    requires = ','.join(sorted(requirements))

    def gen():
        yield 'HGS1'
        yield compression

        filecount, bytecount, it = generatev1(repo)
        repo.ui.status(_('writing %d bytes for %d files\n') %
                         (bytecount, filecount))

        yield struct.pack('>QQ', filecount, bytecount)
        yield struct.pack('>H', len(requires) + 1)
        yield requires + '\0'

        # This is where we'll add compression in the future.
        assert compression == 'UN'

        seen = 0
        repo.ui.progress(_('bundle'), 0, total=bytecount)

        for chunk in it:
            seen += len(chunk)
            repo.ui.progress(_('bundle'), seen, total=bytecount)
            yield chunk

        repo.ui.progress(_('bundle'), None)

    return requirements, gen()

def consumev1(repo, fp, filecount, bytecount):
    """Apply the contents from version 1 of a streaming clone file handle.

    This takes the output from "streamout" and applies it to the specified
    repository.

    Like "streamout," the status line added by the wire protocol is not handled
    by this function.
    """
    lock = repo.lock()
    try:
        repo.ui.status(_('%d files to transfer, %s of data\n') %
                       (filecount, util.bytecount(bytecount)))
        handled_bytes = 0
        repo.ui.progress(_('clone'), 0, total=bytecount)
        start = time.time()

        tr = repo.transaction(_('clone'))
        try:
            for i in xrange(filecount):
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
                    repo.ui.progress(_('clone'), handled_bytes, total=bytecount)
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
                       (util.bytecount(bytecount), elapsed,
                        util.bytecount(bytecount / elapsed)))
    finally:
        lock.release()

def applybundlev1(repo, fp):
    """Apply the content from a stream clone bundle version 1.

    We assume the 4 byte header has been read and validated and the file handle
    is at the 2 byte compression identifier.
    """
    if len(repo):
        raise error.Abort(_('cannot apply stream clone bundle on non-empty '
                            'repo'))

    compression = fp.read(2)
    if compression != 'UN':
        raise error.Abort(_('only uncompressed stream clone bundles are '
            'supported; got %s') % compression)

    filecount, bytecount = struct.unpack('>QQ', fp.read(16))
    requireslen = struct.unpack('>H', fp.read(2))[0]
    requires = fp.read(requireslen)

    if not requires.endswith('\0'):
        raise error.Abort(_('malformed stream clone bundle: '
                            'requirements not properly encoded'))

    requirements = set(requires.rstrip('\0').split(','))
    missingreqs = requirements - repo.supportedformats
    if missingreqs:
        raise error.Abort(_('unable to apply stream clone: '
                            'unsupported format: %s') %
                            ', '.join(sorted(missingreqs)))

    consumev1(repo, fp, filecount, bytecount)

# END COPY OF mercurial/streamclone.py

def capabilities(repo, proto):
    caps = origcapabilities(repo, proto)

    if repo.opener.exists('bundleclone.manifest'):
        caps += ' bundles'

    return caps

def bundles(repo, proto):
    """Server command for returning info for available bundles.

    Clients will parse this response and determine what bundle to fetch.
    """
    return repo.opener.tryread('bundleclone.manifest')

def pull(orig, repo, remote, *args, **kwargs):
    res = orig(repo, remote, *args, **kwargs)

    if not repo.ui.configbool('bundleclone', 'pullmanifest', False):
        return res

    if remote.capable('bundles'):
        lock = repo.lock()
        repo.ui.status(_('pulling bundleclone manifest\n'))
        manifest = remote._call('bundles')
        try:
            repo.opener.write('bundleclone.manifest', manifest)
        finally:
            lock.release()

    # This functionality isn't in upstream Mercurial yet.
    if remote.capable('clonebundles'):
        lock = repo.lock()
        repo.ui.status(_('pulling clonebundles manifest\n'))
        manifest = remote._call('clonebundles')
        try:
            repo.opener.write('clonebundles.manifest', manifest)
        finally:
            lock.release()

    return res


@command('streambundle', [
    ('t', 'type', '', 'type of bundle', 'TYPE'),
], _('hg streambundle [-t TYPE] path'))
def streambundle(ui, repo, path, **opts):
    """Generate a stream bundle file for a repository.

    If ``--type`` is not defined (the default), produce a legacy bundle format.
    Else, produce the requested bundle format, which currently is limited to
    ``S1``.
    """
    typ = opts.get('type', None)
    if not typ:
        requires = set(repo.requirements) & repo.supportedformats
        if requires - set(['revlogv1']):
            raise util.Abort(_('cannot generate stream bundle for this repo '
                'because of requirement: %s') % (' '.join(requires)))

        ui.status(_('writing %s\n') % path)
        with open(path, 'w') as fh:
            for chunk in generatev1wireproto(repo):
                fh.write(chunk)

        ui.write(_('stream bundle file written successully.\n'))
        ui.write(_('include the following in its manifest entry:\n'))
        ui.write('stream=%s\n' % ','.join(requires))
        return

    if typ.lower() != 's1':
        raise error.Abort(_('can only produce s1 bundles'))

    requirements, gen = generatebundlev1(repo)
    with open(path, 'wb') as fh:
        for chunk in gen:
            fh.write(chunk)

    ui.write(_('bundle requirements: %s\n') % ', '.join(sorted(requirements)))


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

            if (exchange and hasattr(exchange, '_maybeapplyclonebundle')
                    and remote.capable('clonebundles')):
                supported = False
                self.ui.warn(_('(mercurial client has built-in support for '
                               'bundle clone features; the "bundleclone" '
                               'extension can likely safely be removed)\n'))

                if not self.ui.configbool('experimental', 'clonebundles', False):
                    self.ui.warn(_('(but the experimental.clonebundles config '
                                   'flag is not enabled: enable it before '
                                   'disabling bundleclone or cloning from '
                                   'pre-generated bundles may not work)\n'))
                    # We assume that presence of the bundleclone extension
                    # means they want clonebundles enabled. Otherwise, why do
                    # they have bundleclone enabled? So silently enable it.
                    ui.setconfig('experimental', 'clonebundles', True)
            elif not remote.capable('bundles'):
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

            pyver = sys.version_info
            pyver = (pyver[0], pyver[1], pyver[2])

            hgver = util.version()
            # Discard bit after '+'.
            hgver = hgver.split('+')[0]
            try:
                hgver = tuple([int(i) for i in hgver.split('.')[0:2]])
            except ValueError:
                hgver = (0, 0)

            # Testing backdoors.
            if ui.config('bundleclone', 'fakepyver'):
                pyver = ui.configlist('bundleclone', 'fakepyver')
                pyver = tuple(int(v) for v in pyver)

            if ui.config('bundleclone', 'fakehgver'):
                hgver = ui.configlist('bundleclone', 'fakehgver')
                hgver = tuple(int(v) for v in hgver[0:2])

            entries = []
            snifilteredfrompython = False
            snifilteredfromhg = False

            for line in result.splitlines():
                fields = line.split()
                url = fields[0]
                attrs = {}
                for rawattr in fields[1:]:
                    key, value = rawattr.split('=', 1)
                    attrs[urllib.unquote(key)] = urllib.unquote(value)

                # Filter out SNI entries if we don't support SNI.
                if attrs.get('requiresni') == 'true':
                    skip = False
                    if pyver < (2, 7, 9):
                        # Take this opportunity to inform people they are using an
                        # old, insecure Python.
                        if not snifilteredfrompython:
                            self.ui.warn(_('(your Python is older than 2.7.9 '
                                           'and does not support modern and '
                                           'secure SSL/TLS; please consider '
                                           'upgrading your Python to a secure '
                                           'version)\n'))
                        snifilteredfrompython = True
                        skip = True

                    if hgver < (3, 3):
                        if not snifilteredfromhg:
                            self.ui.warn(_('(you Mercurial is old and does '
                                           'not support modern and secure '
                                           'SSL/TLS; please consider '
                                           'upgrading your Mercurial to 3.3+ '
                                           'which supports modern and secure '
                                           'SSL/TLS)\n'))
                        snifilteredfromhg = True
                        skip = True

                    if skip:
                        self.ui.warn(_('(ignoring URL on server that requires '
                                       'SNI)\n'))
                        continue

                entries.append((url, attrs))

            if not entries:
                # Don't fall back to normal clone because we don't want mass
                # fallback in the wild to barage servers expecting bundle
                # offload.
                raise util.Abort(_('no appropriate bundles available'),
                                 hint=_('you may wish to complain to the '
                                        'server operator'))

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
                    l = fh.readline()
                    filecount, bytecount = map(int, l.split(' ', 1))
                    self.ui.status(_('streaming all changes\n'))
                    consumev1(self, fh, filecount, bytecount)
                else:
                    if exchange:
                        cg = exchange.readbundle(self.ui, fh, 'stream')
                    else:
                        cg = changegroup.readbundle(fh, 'stream')

                    # Mercurial 3.6 introduced cgNunpacker.apply().
                    # Before that, there was changegroup.addchangegroup().
                    # Before that, there was localrepository.addchangegroup().
                    if hasattr(cg, 'apply'):
                        cg.apply(self, 'bundleclone', url)
                    elif hasattr(changegroup, 'addchangegroup'):
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
