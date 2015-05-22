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

This metadata is optional. No metadata is currently defined by this extension:
it is completely up to server operators to define their own metadata. See below
on use cases.

The server operator is responsible for generating the bundle manifest file.

While the bundle manifest can consist of multiple lines, the client will
currently only consult the first line.

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

"""

import urllib
import urllib2

from mercurial import (
    changegroup,
    cmdutil,
    extensions,
    url as hgurl,
    wireproto,
)
from mercurial.i18n import _

testedwith = '3.1 3.2 3.3 3.4'
buglink = 'https://bugzilla.mozilla.org/enter_bug.cgi?product=Developer%20Services&component=Mercurial%3A%20bundleclone'

cmdtable = {}
command = cmdutil.command(cmdtable)

origcapabilities = wireproto.capabilities

from mercurial import exchange

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

def extsetup(ui):
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

            url = entries[0][0]

            if not url:
                self.ui.note(_('invalid bundle manifest; using normal clone\n'))
                return super(bundleclonerepo, self).clone(remote, heads=heads,
                        stream=stream)

            self.ui.status(_('downloading bundle %s\n' % url))

            try:
                fh = hgurl.open(self.ui, url)
                cg = exchange.readbundle(self.ui, fh, 'stream')

                changegroup.addchangegroup(self, cg, 'bundleclone', url)

                self.ui.status(_('finishing applying bundle; pulling\n'))
                return exchange.pull(self, remote, heads=heads)

            except urllib2.HTTPError as e:
                self.ui.warn(_('HTTP error fetching bundle; using normal clone: %s\n') % str(e))
                return super(bundleclonerepo, self).clone(remote, heads=heads,
                        stream=stream)
            # This typically means a connectivity, DNS, etc problem.
            except urllib2.URLError as e:
                self.ui.warn(_('error fetching bundle; using normal clone: %s\n') % e.reason)
                return super(bundleclonerepo, self).clone(remote, heads=heads,
                        stream=stream)

    repo.__class__ = bundleclonerepo
