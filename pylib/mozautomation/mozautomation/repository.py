# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import unicode_literals

import requests

TREE_ALIASES = {
    b'mozilla-central': (b'central',),
    b'mc': (b'central',),
    b'm-c': (b'central',),
    b'mozilla-inbound': (b'inbound',),
    b'm-i': (b'inbound',),
    b'mi': (b'inbound',),
    b'inbound': (b'inbound',),
    b'in': (b'inbound',),
    b'fx': (b'fx-team',),
    b'mozilla-services': (b'services',),
    b's-c': (b'services',),
    b'sc': (b'services',),
    b'bs': (b'build',),
    b'b-s': (b'build',),
    b'build-system': (b'build',),
    b'gfx': (b'graphics',),
    b'mozilla-release': (b'release',),
    b'mozilla-aurora': (b'aurora',),
    b'mozilla-beta': (b'beta',),
    b'mozilla-b2g32': (b'b2g32',),
    b'mozilla-b2g34': (b'b2g34',),
    b'mozilla-b2g37': (b'b2g37',),
    b'mozilla-b2g44': (b'b2g44',),
    b'b2g-inbound': (b'b2ginbound',),
    b'b2g': (b'b2ginbound',),
    b'b-i': (b'b2ginbound',),
    b'b2g-ota': (b'b2g-ota',),
    b'comm-central': (b'comm',),
    b'c-c': (b'comm',),
    b'cc': (b'comm',),
    b'c-a': (b'comm-aurora',),
    b'ca': (b'comm-aurora',),
    b'c-b': (b'comm-beta',),
    b'cb': (b'comm-beta',),
    b'c-r': (b'comm-release',),
    b'cr': (b'comm-release',),

    b'releases': (b'esr91', b'esr102', b'release', b'beta', b'aurora', b'central'),
    b'integration': (b'inbound', b'fx-team', b'autoland'),
    b'twigs': (
        b'alder',
        b'ash', 
        b'birch',
        b'cedar',
        b'toolchains',
        b'cypress',
        b'date',
        b'elm',
        b'fig',
        b'gum',
        b'holly',
        b'jamun',
        b'kaios',
        b'larch',
        b'maple',
        b'oak',
        b'pine',
        b'pine-stable',
        b'stylo',
    ),
    b'obsolete': (b'esr10', b'esr17', b'b2ginbound', b'b2g18', b'esr24', b'esr31',
                 b'esr38', b'esr45', b'esr52', b'esr60', b'esr68', b'esr78',
                 b'b2g26', b'b2g28', b'b2g30', b'b2g32',
                 b'b2g34', b'b2g37', b'b2g44', b'b2g-ota'),
}

# Aliases that map to multiple repositories.
MULTI_TREE_ALIASES = {}
for tree, aliases in TREE_ALIASES.items():
    if len(aliases) > 1:
        MULTI_TREE_ALIASES[tree] = aliases

BASE_READ_URI = b'https://hg.mozilla.org/'
BASE_WRITE_URI = b'ssh://hg.mozilla.org/'

REPOS = {
    # Release repositories.
    b'central': b'mozilla-central',
    b'aurora': b'releases/mozilla-aurora',
    b'beta': b'releases/mozilla-beta',
    b'release': b'releases/mozilla-release',
    b'esr10': b'releases/mozilla-esr10',
    b'esr17': b'releases/mozilla-esr17',
    b'esr24': b'releases/mozilla-esr24',
    b'esr31': b'releases/mozilla-esr31',
    b'esr38': b'releases/mozilla-esr38',
    b'esr45': b'releases/mozilla-esr45',
    b'esr52': b'releases/mozilla-esr52',
    b'esr60': b'releases/mozilla-esr60',
    b'esr68': b'releases/mozilla-esr68',
    b'esr78': b'releases/mozilla-esr78',
    b'esr91': b'releases/mozilla-esr91',
    b'esr102': b'releases/mozilla-esr102',
    b'b2g18': b'releases/mozilla-b2g18',
    b'b2g26': b'releases/mozilla-b2g26_v1_2',
    b'b2g28': b'releases/mozilla-b2g28_v1_3',
    b'b2g30': b'releases/mozilla-b2g30_v1_4',
    b'b2g32': b'releases/mozilla-b2g32_v2_0',
    b'b2g34': b'releases/mozilla-b2g34_v2_1',
    b'b2g37': b'releases/mozilla-b2g37_v2_2',
    b'b2g44': b'releases/mozilla-b2g44_v2_5',
    b'b2g-ota': b'releases/b2g-ota',

    # Integration repositories.
    b'autoland': b'integration/autoland',
    b'b2ginbound': b'integration/b2g-inbound',
    b'build': b'projects/build-system',
    b'fx-team': b'integration/fx-team',
    b'graphics': b'projects/graphics',
    b'inbound': b'integration/mozilla-inbound',
    b'places': b'projects/places',
    b'services': b'services/services-central',

    # Twigs
    b'alder': b'projects/alder',
    b'ash': b'projects/ash',
    b'birch': b'projects/birch',
    b'cedar': b'projects/cedar',
    b'toolchains': b'projects/toolchains',
    b'cypress': b'projects/cypress',
    b'date': b'projects/date',
    b'elm': b'projects/elm',
    b'fig': b'projects/fig',
    b'gum': b'projects/gum',
    b'holly': b'projects/holly',
    b'jamun': b'projects/jamun',
    b'kaios': b'projects/kaios',
    b'larch': b'projects/larch',
    b'maple': b'projects/maple',
    b'oak': b'projects/oak',
    b'pine': b'projects/pine',
    b'pine-stable': b'projects/pine-stable',
    b'stylo': b'incubator/stylo',

    # Comm repositories.
    b'comm': b'comm-central',
    b'comm-aurora': b'releases/comm-aurora',
    b'comm-beta': b'releases/comm-beta',
    b'comm-release': b'releases/comm-release',
    b'comm-esr10': b'releases/comm-esr10',
    b'comm-esr17': b'releases/comm-esr17',
    b'comm-esr24': b'releases/comm-esr24',
    b'comm-esr31': b'releases/comm-esr31',
    b'comm-esr38': b'releases/comm-esr38',
    b'comm-esr45': b'releases/comm-esr45',
    b'comm-esr52': b'releases/comm-esr52',
    b'comm-esr60': b'releases/comm-esr60',
    b'comm-esr68': b'releases/comm-esr68',
    b'comm-esr78': b'releases/comm-esr78',
    b'comm-esr91': b'releases/comm-esr91',
    b'comm-esr102': b'releases/comm-esr102',

    # Misc
    b'try': b'try',
    b'try-comm': b'try-comm-central',

    # KaiOS
    b'kaios': b'projects/kaios',
    b'kaios-try': b'projects/kaios-try',
}

OFFICIAL_MAP = {
    b'central': b'mozilla-central',
    b'inbound': b'mozilla-inbound',
    b'services': b'services-central',
    b'release': b'mozilla-release',
    b'aurora': b'mozilla-aurora',
    b'beta': b'mozilla-beta',
    b'build': b'build-system',
    b'esr17': b'mozilla-esr17',
    b'esr24': b'mozilla-esr24',
    b'esr31': b'mozilla-esr31',
    b'esr38': b'mozilla-esr38',
    b'esr45': b'mozilla-esr45',
    b'esr52': b'mozilla-esr52',
    b'esr60': b'mozilla-esr60',
    b'esr68': b'mozilla-esr68',
    b'esr78': b'mozilla-esr78',
    b'esr91': b'mozilla-esr91',
    b'esr102': b'mozilla-esr102',
}

RELEASE_TREES = set([
    b'central',
    b'aurora',
    b'beta',
    b'release',
    b'b2g18',
    b'esr17',
    b'esr24',
    b'b2g26',
    b'b2g28',
    b'b2g30',
    b'esr31',
    b'esr38',
    b'esr45',
    b'esr52',
    b'esr60',
    b'esr68',
    b'esr78',
    b'esr91',
    b'esr102',
    b'b2g32',
    b'b2g34',
    b'b2g37',
    b'b2g44',
    b'b2g-ota',
])


TRY_TREES = set([
    b'try',
    b'try-comm',
    b'kaios-try',
])

def resolve_trees_to_official(trees):
    mapped = []
    for tree in trees:
        mapped.extend(TREE_ALIASES.get(tree, [tree]))
    mapped = [OFFICIAL_MAP.get(tree, tree) for tree in mapped]

    return mapped


def resolve_trees_to_uris(trees, write_access=False):
    """Resolve tree names to repositories URIs.

    The caller passes in an iterable of tree names. These can be common names,
    aliases, or official names.

    A list of 2-tuples is returned. If a repository could be resolved to a URI,
    the tuple is (common_name, uri). If a repository could not be resolved to a
    URI, the tuple is (specified_name, None).
    """
    mapped = []
    for tree in trees:
        mapped.extend(TREE_ALIASES.get(tree, [tree]))
    repos = [REPOS.get(tree, None) for tree in mapped]

    base = BASE_WRITE_URI if write_access else BASE_READ_URI

    uris = []
    for i, tree in enumerate(repos):
        if tree is None:
            uris.append((trees[i], None))
        else:
            uris.append((mapped[i], b'%s%s' % (base, tree)))

    return uris


def resolve_uri_to_tree(uri):
    """Try to resolve a URI back to a known tree."""
    # Account for a trailing `/`.
    if uri.endswith(b'/'):
        uri = uri[:-1]

    for tree, path in REPOS.items():
        # Try `https` URI first.
        read_url_https = b'%s%s' % (BASE_READ_URI, path)
        if uri == read_url_https:
            return tree

        # Try `http` URI next.
        read_url_http = read_url_https.replace(b'https://', b'http://')
        if uri == read_url_http:
            return tree

        # Try `ssh` URI last.
        write_url_ssh = b'%s%s' % (BASE_WRITE_URI, path)
        if uri == write_url_ssh:
            return tree

    return None


def treeherder_url(tree, rev):
    """Obtain the Treeherder url for a push."""
    tree = resolve_trees_to_official([tree])[0]

    if not tree:
        return None

    return b'https://treeherder.mozilla.org/jobs?repo=%s&revision=%s' % (tree, rev)


class PushInfo(object):
    """Represents an entry from the repository pushlog."""

    def __init__(self, push_id, d):
        self.push_id = push_id
        self.date = d[b'date']
        self.changesets = []

        for changeset in d[b'changesets']:
            entry = changeset
            entry[b'tags'] = set(entry[b'tags']) if entry[b'tags'] else set()
            self.changesets.append(entry)

    @property
    def nodes(self):
        """All the changesets pushed in this push."""
        return [c[b'node'] for c in self.changesets]

    @property
    def first_node(self):
        return self.nodes[0]

    @property
    def last_node(self):
        return self.nodes[-1]


class MercurialRepository(object):
    """Interface with a Mozilla Mercurial repository."""

    def __init__(self, url):
        self.url = url

    def push_info_for_changeset(self, changeset):
        """Obtain the push information for a single changeset.

        Returns a PushInfo on success or None if no push info is available.
        """
        o = requests.get(b'%s/json-pushes?full=1&changeset=%s' % ( self.url,
            changeset)).json()

        if not o:
            return None

        push_id = o.keys()[0]
        return PushInfo(push_id, o[push_id])

    def push_info(self, full=False, start_id=0):
        """Obtain all pushlog info for a repository."""

        url = b'%s/json-pushes?startID=%d' % (self.url, start_id)
        if full:
            url += b'&full=1'
        pushes = requests.get(url).json()

        for push_id in sorted(int(k) for k in pushes):
            yield push_id, pushes[str(push_id)]
