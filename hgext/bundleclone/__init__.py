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

That is, a URL followed by extra metadata describing it. This metadata is
optional. No metadata is currently defined. It is reserved for future use to
enable things such as clients choosing an appropriate bundle. For example,
clients on slow connections may wish to choose a bz2 bundle whereas clients
on fast connections may wish to choose an uncompressed bundle.

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
"""

import urllib2

from mercurial import (
    changegroup,
    cmdutil,
    extensions,
    url as hgurl,
    wireproto,
)
from mercurial.i18n import _

testedwith = '2.5.4 2.6 2.6.1 2.6.2 2.6.3 2.7 2.7.1 2.7.2 2.8 2.8.1 2.8.2 2.9 2.9.1 2.9.2 3.0 3.0.1 3.0.2 3.1'
buglink = 'https://bugzilla.mozilla.org/enter_bug.cgi?product=Developer%20Services&component=Mercurial:%20bundleclone'

cmdtable = {}
command = cmdutil.command(cmdtable)

origcapabilities = wireproto.capabilities

try:
    from mercurial import exchange
    readbundle = exchange.readbundle
except ImportError:
    readbundle = changegroup.readbundle

def capabilities(*args, **kwargs):
    return origcapabilities(*args, **kwargs) + ' bundles'

def bundles(repo, proto):
    """Server command for returning info for available bundles.

    Clients will parse this response and determine what bundle to fetch.
    """
    return repo.opener.tryread('bundleclone.manifest')

def extsetup(ui):
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

            # Eventually we'll support choosing the best options. Until then,
            # use the first entry.
            entry = result.splitlines()[0]
            fields = entry.split()
            url = fields[0]

            if not url:
                self.ui.note(_('invalid bundle manifest; using normal clone\n'))
                return super(bundleclonerepo, self).clone(remote, heads=heads,
                        stream=stream)

            self.ui.status(_('downloading bundle %s\n' % url))

            try:
                fh = hgurl.open(self.ui, url)
                # Newer versions of readbundle take a ui argument.
                try:
                    cg = readbundle(self.ui, fh, 'stream')
                except TypeError:
                    cg = readbundle(fh, 'stream')

                # addchangegroup moved from localrepo class to changegroup module.
                if hasattr(changegroup, 'addchangegroup'):
                    changegroup.addchangegroup(self, cg, 'bundleclone', url)
                else:
                    self.addchangegroup(cg, 'bundleclone', url)

                self.ui.status(_('finishing applying bundle; pulling\n'))
                return self.pull(remote, heads=heads)

            except urllib2.HTTPError as e:
                self.ui.warn(_('HTTP error fetching bundle; using normal clone: %s\n') % str(e))
                return super(bundleclonerepo, self).clone(remote, heads=heads,
                        stream=stream)
            # This typically means a connectivity, DNS, etc problem.
            except urllib2.URLError as e:
                self.ui.warn(_('error fetching bundle; using normal clone: %s\n') % e.reason)
                return super(bundleclonerepo, self).clone(remote, heads=heads,
                        stream=stream)

        def pull(self, remote, *args, **kwargs):
            res = super(bundleclonerepo, self).pull(remote, *args, **kwargs)

            if remote.capable('bundles') and \
                    self.ui.configbool('bundleclone', 'pullmanifest', False):

                lock = self.lock()
                self.ui.status(_('pulling bundleclone manifest\n'))
                manifest = remote._call('bundles')
                try:
                    self.opener.write('bundleclone.manifest', manifest)
                finally:
                    lock.release()

            return res

    repo.__class__ = bundleclonerepo
