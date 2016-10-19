# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

import grp
import os


def can_push(user):
    # Members of the autoland group can push.
    try:
        g = grp.getgrnam('scm_autoland')
        if user in g.gr_mem:
            return True
    except KeyError:
        pass

    # Selected users who have pushed recently can also push.
    return user in {
        'ahunt@mozilla.com',
        'apoirot@mozilla.com',
        'bgrinstead@mozilla.com',
        'florian@queze.net',
        'gabriel.luong@gmail.com',
        'jdescottes@mozilla.com',
        'jlong@mozilla.com',
        'mozilla@noorenberghe.ca',
        'ntim.bugs@gmail.com',
    }


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
    ui.write('The repository became read-only on October 19 except to\n')
    ui.write('sheriffs and people who have pushed recently. The repository\n')
    ui.write('will be read-only to everyone starting on November 1.\n')
    ui.write('\n')

    if can_push(os.environ['USER']):
        ui.write('Please start changing your development workflow to base commits\n')
        ui.write('off of mozilla-central instead of fx-team.\n')
        ui.write('\n')
        ui.write('Please consider landing commits via MozReview+Autoland (preferred)\n')
        ui.write('or to mozilla-inbound. (mozilla-inbound will eventually go away too\n')
        ui.write('so use of Autoland is highly encouraged.)\n')
        ui.write('%s\n' % header)
        return 0
    else:
        ui.write('YOU NO LONGER HAVE PUSH ACCESS TO FX-TEAM.\n')
        ui.write('\n')
        ui.write('Please land commits via MozReview+Autoland. Or, use\n')
        ui.write('mozilla-inbound (but it will be going away eventually too)\n')
        ui.write('%s\n' % header)
        return 1
