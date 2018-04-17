# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import unicode_literals

import requests

TREE_ALIASES = {
    'mozilla-central': ('central',),
    'mc': ('central',),
    'm-c': ('central',),
    'mozilla-inbound': ('inbound',),
    'm-i': ('inbound',),
    'mi': ('inbound',),
    'inbound': ('inbound',),
    'in': ('inbound',),
    'fx': ('fx-team',),
    'mozilla-services': ('services',),
    's-c': ('services',),
    'sc': ('services',),
    'bs': ('build',),
    'b-s': ('build',),
    'build-system': ('build',),
    'gfx': ('graphics',),
    'mozilla-release': ('release',),
    'mozilla-aurora': ('aurora',),
    'mozilla-beta': ('beta',),
    'mozilla-b2g32': ('b2g32',),
    'mozilla-b2g34': ('b2g34',),
    'mozilla-b2g37': ('b2g37',),
    'mozilla-b2g44': ('b2g44',),
    'b2g-inbound': ('b2ginbound',),
    'b2g': ('b2ginbound',),
    'b-i': ('b2ginbound',),
    'b2g-ota': ('b2g-ota',),
    'comm-central': ('comm',),
    'c-c': ('comm',),
    'cc': ('comm',),
    'c-a': ('comm-aurora',),
    'ca': ('comm-aurora',),
    'c-b': ('comm-beta',),
    'cb': ('comm-beta',),
    'c-r': ('comm-release',),
    'cr': ('comm-release',),

    'releases': ('esr60', 'esr52', 'release', 'beta', 'aurora', 'central'),
    'integration': ('inbound', 'fx-team', 'autoland'),
    'twigs': ('alder', 'ash', 'birch', 'cedar', 'cypress', 'date', 'elm',
              'fig', 'gum', 'holly', 'jamun', 'larch', 'maple', 'oak', 'pine',
              'stylo'),
    'obsolete': ('esr10', 'esr17', 'b2ginbound', 'b2g18', 'esr24', 'esr31',
                 'esr38', 'esr45', 'b2g26', 'b2g28', 'b2g30', 'b2g32', 'b2g34',
                 'b2g37', 'b2g44', 'b2g-ota'),
}

# Aliases that map to multiple repositories.
MULTI_TREE_ALIASES = {}
for tree, aliases in TREE_ALIASES.items():
    if len(aliases) > 1:
        MULTI_TREE_ALIASES[tree] = aliases

BASE_READ_URI = 'https://hg.mozilla.org/'
BASE_WRITE_URI = 'ssh://hg.mozilla.org/'

REPOS = {
    # Release repositories.
    'central': 'mozilla-central',
    'aurora': 'releases/mozilla-aurora',
    'beta': 'releases/mozilla-beta',
    'release': 'releases/mozilla-release',
    'esr10': 'releases/mozilla-esr10',
    'esr17': 'releases/mozilla-esr17',
    'esr24': 'releases/mozilla-esr24',
    'esr31': 'releases/mozilla-esr31',
    'esr38': 'releases/mozilla-esr38',
    'esr45': 'releases/mozilla-esr45',
    'esr52': 'releases/mozilla-esr52',
    'b2g18': 'releases/mozilla-b2g18',
    'b2g26': 'releases/mozilla-b2g26_v1_2',
    'b2g28': 'releases/mozilla-b2g28_v1_3',
    'b2g30': 'releases/mozilla-b2g30_v1_4',
    'b2g32': 'releases/mozilla-b2g32_v2_0',
    'b2g34': 'releases/mozilla-b2g34_v2_1',
    'b2g37': 'releases/mozilla-b2g37_v2_2',
    'b2g44': 'releases/mozilla-b2g44_v2_5',
    'b2g-ota': 'releases/b2g-ota',

    # Integration repositories.
    'autoland': 'integration/autoland',
    'b2ginbound': 'integration/b2g-inbound',
    'build': 'projects/build-system',
    'fx-team': 'integration/fx-team',
    'graphics': 'projects/graphics',
    'inbound': 'integration/mozilla-inbound',
    'places': 'projects/places',
    'services': 'services/services-central',

    # Twigs
    'alder': 'projects/alder',
    'ash': 'projects/ash',
    'birch': 'projects/birch',
    'cedar': 'projects/cedar',
    'cypress': 'projects/cypress',
    'date': 'projects/date',
    'elm': 'projects/elm',
    'fig': 'projects/fig',
    'gum': 'projects/gum',
    'holly': 'projects/holly',
    'jamun': 'projects/jamun',
    'larch': 'projects/larch',
    'maple': 'projects/maple',
    'oak': 'projects/oak',
    'pine': 'projects/pine',
    'stylo': 'incubator/stylo',

    # Comm repositories.
    'comm': 'comm-central',
    'comm-aurora': 'releases/comm-aurora',
    'comm-beta': 'releases/comm-beta',
    'comm-release': 'releases/comm-release',
    'comm-esr10': 'releases/comm-esr10',
    'comm-esr17': 'releases/comm-esr17',
    'comm-esr24': 'releases/comm-esr24',
    'comm-esr31': 'releases/comm-esr31',
    'comm-esr38': 'releases/comm-esr38',
    'comm-esr45': 'releases/comm-esr45',
    'comm-esr52': 'releases/comm-esr52',

    # Misc
    'try': 'try',
    'try-comm': 'try-comm-central',
}

OFFICIAL_MAP = {
    'central': 'mozilla-central',
    'inbound': 'mozilla-inbound',
    'services': 'services-central',
    'release': 'mozilla-release',
    'aurora': 'mozilla-aurora',
    'beta': 'mozilla-beta',
    'build': 'build-system',
    'esr17': 'mozilla-esr17',
    'esr24': 'mozilla-esr24',
    'esr31': 'mozilla-esr31',
    'esr38': 'mozilla-esr38',
    'esr45': 'mozilla-esr45',
    'esr52': 'mozilla-esr52',
    'esr60': 'mozilla-esr60',
}

RELEASE_TREES = set([
    'central',
    'aurora',
    'beta',
    'release',
    'b2g18',
    'esr17',
    'esr24',
    'b2g26',
    'b2g28',
    'b2g30',
    'esr31',
    'esr38',
    'esr45',
    'esr52',
    'esr60',
    'b2g32',
    'b2g34',
    'b2g37',
    'b2g44',
    'b2g-ota',
])


TRY_TREES = set([
    'try',
    'try-comm',
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
            uris.append((mapped[i], '%s%s' % (base, tree)))

    return uris


def resolve_uri_to_tree(uri):
    """Try to resolve a URI back to a known tree."""

    for tree, path in REPOS.items():
        if uri.startswith('%s%s' % (BASE_READ_URI, path)):
            return tree

        if uri.startswith('%s%s' % (
            BASE_READ_URI.replace('https://', 'http://'),
            path)):
            return tree

        if uri.startswith('%s%s' % (BASE_WRITE_URI, path)):
            return tree

    return None


def treeherder_url(tree, rev):
    """Obtain the Treeherder url for a push."""
    tree = resolve_trees_to_official([tree])[0]

    if not tree:
        return None

    return 'https://treeherder.mozilla.org/#/jobs?repo=%s&revision=%s' % (tree, rev)


class PushInfo(object):
    """Represents an entry from the repository pushlog."""

    def __init__(self, push_id, d):
        self.push_id = push_id
        self.date = d['date']
        self.changesets = []

        for changeset in d['changesets']:
            entry = changeset
            entry['tags'] = set(entry['tags']) if entry['tags'] else set()
            self.changesets.append(entry)

    @property
    def nodes(self):
        """All the changesets pushed in this push."""
        return [c['node'] for c in self.changesets]

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
        o = requests.get('%s/json-pushes?full=1&changeset=%s' % ( self.url,
            changeset)).json()

        if not o:
            return None

        push_id = o.keys()[0]
        return PushInfo(push_id, o[push_id])

    def push_info(self, full=False, start_id=0):
        """Obtain all pushlog info for a repository."""

        url = '%s/json-pushes?startID=%d' % (self.url, start_id)
        if full:
            url += '&full=1'
        pushes = requests.get(url).json()

        for push_id in sorted(int(k) for k in pushes):
            yield push_id, pushes[str(push_id)]
