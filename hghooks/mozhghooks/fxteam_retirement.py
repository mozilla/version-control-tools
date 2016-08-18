# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

def hook(ui, repo, source=None, **kwargs):
    if source in ('pull', 'strip'):
        return 0

    # Don't print message on merge commits.
    if len(repo['tip'].parents()) > 1:
        return 0

    header = '*' * 72
    ui.write('%s\n' % header)
    ui.write('The fx-team repository is in the process of being retired.\n')
    ui.write('\n')
    ui.write('Push access to this repository will be going away.\n')
    ui.write('\n')
    ui.write('Please start changing your development workflow to base commits\n')
    ui.write('off of mozilla-central instead of fx-team.\n')
    ui.write('\n')
    ui.write('Please consider landing commits via MozReview+Autoland (preferred)\n')
    ui.write('or to mozilla-inbound. (mozilla-inbound will eventually go away too\n')
    ui.write('so use of Autoland is highly encouraged.)\n')
    ui.write('%s\n' % header)

    return 0
