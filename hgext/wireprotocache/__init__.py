# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

'''Support for caching wire protocol version 2 objects

This extension provides drop-in plugins for CBOR encoded
objects in the Mercurial wire protocol version 2.

::

    [extensions]
    # turn on the extension
    wireprotocache =
    [wireprotocache]
    # select which cacher to use
    plugin = s3
    [wireprotocache.s3]
    # configure plugin specific options
    # see the docstrings of the modules for more info
'''
import importlib

from mercurial import (
    demandimport,
    extensions,
    registrar,
    util,
    wireprotov2server,
)

cache_module_attrs = {
    'makeresponsecacher',
    'getadvertisedredirecttargets',
}

minimumhgversion = '4.8'
testedwith = '4.8'

configtable = {}
configitem = registrar.configitem(configtable)

configitem('wireprotocache', 'plugin',
           default=None)

# TODO find a way to move these into the s3 module
configitem('wireprotocache.s3', 'access-key-id',
           default=None)
configitem('wireprotocache.s3', 'bucket',
           default=None)
configitem('wireprotocache.s3', 'cacheacl',
           default='public-read')
configitem('wireprotocache.s3', 'delete-repo-keystate',
           default=False)
configitem('wireprotocache.s3', 'endpoint-url',
           default=None)
configitem('wireprotocache.s3', 'minimumobjectsize',
           default=None)
configitem('wireprotocache.s3', 'redirecttargets',
           default=None)
configitem('wireprotocache.s3', 'secret-access-key',
           default=None)


def extsetup(ui):
    '''Dynamically import the cache plugin and monkeypatch
    the required functions to enable caching
    '''
    plugin = ui.config('wireprotocache', 'plugin')

    # grab the correct import name from the __module__
    # value of this function. expecting a value like
    # `hgext_wireprotocache` due to the way Mercurial
    # loads extensions
    module = '%s.%s' % (extsetup.__module__, plugin)

    with demandimport.deactivated():
        cache_module = importlib.import_module(module)

    # Ensure the imported module has the required patching functions
    for attr in cache_module_attrs:
        assert util.safehasattr(cache_module, attr), \
            'function %s missing from %s' % (attr, plugin)

    extensions.wrapfunction(wireprotov2server, 'makeresponsecacher',
                            cache_module.makeresponsecacher)
    extensions.wrapfunction(wireprotov2server, 'getadvertisedredirecttargets',
                            cache_module.getadvertisedredirecttargets)
