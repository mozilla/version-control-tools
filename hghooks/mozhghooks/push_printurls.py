#!/usr/bin/python
import os.path
from mercurial.node import short

hgNameToRevURL = {
    # Gecko trunk / integration branches
    'b2g-inbound':      'integration/b2g-inbound/',
    'build-system':     'projects/build-system',
    'fx-team':          'integration/fx-team/',
    'mozilla-central':  'mozilla-central/',
    'mozilla-inbound':  'integration/mozilla-inbound/',
    'services-central': 'services/services-central/',
    # Gecko release branches
    'mozilla-aurora':  'releases/mozilla-aurora/',
    'mozilla-beta':    'releases/mozilla-beta/',
    'mozilla-release': 'releases/mozilla-release/',
    'mozilla-esr24':   'releases/mozilla-esr24/',
    'mozilla-esr31':   'releases/mozilla-esr31/',
    # Gecko B2G branches
    'mozilla-b2g34_v2_1s':     'releases/mozilla-b2g34_v2_1s/',
    'mozilla-b2g34_v2_1':      'releases/mozilla-b2g34_v2_1/',
    'mozilla-b2g32_v2_0':      'releases/mozilla-b2g32_v2_0/',
    'mozilla-b2g30_v1_4':      'releases/mozilla-b2g30_v1_4/',
    'mozilla-b2g28_v1_3':      'releases/mozilla-b2g28_v1_3/',
    'mozilla-b2g28_v1_3t':     'releases/mozilla-b2g28_v1_3t/',
    # Thunderbird branches
    'comm-central': 'comm-central/',
    'comm-aurora':  'releases/comm-aurora/',
    'comm-beta':    'releases/comm-beta/',
    'comm-release': 'releases/comm-release/',
    'comm-esr24':   'releases/comm-esr24/',
    'comm-esr31':   'releases/comm-esr31/',
    # Try repos
    'try':              'try/',
    'try-comm-central': 'try-comm-central/',
}

# Project branches that are in active use
hgNameToRevURL.update({
    'alder':   'projects/alder/',
    'ash':     'projects/ash/',
    'birch':   'projects/birch/',
    'cedar':   'projects/cedar/',
    'cypress': 'projects/cypress/',
    'date':    'projects/date/',
    'elm':     'projects/elm/',
    'fig':     'projects/fig/',
    'gum':     'projects/gum/',
    'holly':   'projects/holly/',
    'jamun':   'projects/jamun/',
    'larch':   'projects/larch/',
    'maple':   'projects/maple/',
    'oak':     'projects/oak/',
    'pine':    'projects/pine/',
})

# QA repos
hgNameToRevURL.update({
    'mozmill-tests':        'qa/mozmill-tests/',
    'testcase-data':        'qa/testcase-data/',
})

# RelEng repos
hgNameToRevURL.update({
    'autoland':             'build/autoland/',
    'braindump':            'build/braindump/',
    'buildapi':             'build/buildapi/',
    'buildbot':             'build/buildbot/',
    'buildbot-configs':     'build/buildbot-configs/',
    'buildbotcustom':       'build/buildbotcustom/',
    'cloud-tools':          'build/cloud-tools/',
    'compare-locales':      'build/compare-locales/',
    'fork-hg-git':          'build/fork-hg-git/',
    'hghooks':              'hgcustom/hghooks/',
    'mozharness':           'build/mozharness/',
    'mozpool':              'build/mozpool/',
    'opsi-package-sources': 'build/opsi-package-sources/',
    'partner-repacks':      'build/partner-repacks/',
    'preproduction':        'build/preproduction/',
    'puppet':               'build/puppet/',
    'puppet-manifests':     'build/puppet-manifests/',
    'rpm-sources':          'build/rpm-sources/',
    'talos':                'build/talos/',
    'tbpl':                 'webtools/tbpl/',
    'tools':                'build/tools/',
    'twisted':              'build/twisted/',
})


def hook(ui, repo, node, hooktype, **kwargs):
    repo_name = os.path.basename(repo.root)
    if repo_name not in hgNameToRevURL:
        return 0

    # All changesets from node to "tip" inclusive are part of this push.
    rev = repo.changectx(node).rev()
    tip = repo.changectx('tip').rev()

    num_changes = tip + 1 - rev
    url = 'https://hg.mozilla.org/' + hgNameToRevURL[repo_name]

    if num_changes <= 10:
        plural = 's' if num_changes > 1 else ''
        print 'You can view your change%s at the following URL%s:' % (plural, plural)

        for i in xrange(rev, tip + 1):
            node = short(repo.changectx(i).node())
            print '  %srev/%s' % (url, node)
    else:
        tip_node = short(repo.changectx(tip).node())
        print 'You can view the pushlog for your changes at the following URL:'
        print '  %spushloghtml?changeset=%s' % (url, tip_node)

    # For try repositories, also output a results dashboard url.
    if repo_name in ['try', 'try-comm-central']:
        tip_node = short(repo.changectx(tip).node())
        # TBPL uses alternative names that don't match buildbot or hg.
        tbpl_name = 'Thunderbird-Try' if repo_name == 'try-comm-central' else 'Try'
        print 'You can view the progress of your build at the following URL:'
        print '  https://treeherder.mozilla.org/#/jobs?repo=%s&revision=%s' % (repo_name, tip_node)
        print 'Alternatively, view them on TBPL (soon to be deprecated):'
        print '  https://tbpl.mozilla.org/?tree=%s&rev=%s' % (tbpl_name, tip_node)

    return 0
