# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

"""Hook that prevents bookmarks from being set.

It may not prevent bookmark setting via all scenarios. The main aim is to
prevent bookmark pushing via the wire protocol.
"""

def hook(ui, repo, hooktype, namespace, key, old, new, source=None, **kwargs):
    if source in ('pull', 'strip'):
        return 0

    if namespace != 'bookmarks':
        return 0

    ui.write('bookmarks are disabled on this repository; '
             'refusing to accept modification to "%s"\n' % key)
    return 1
