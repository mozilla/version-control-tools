#!/usr/bin/env python
# This software may be used and distributed according to the terms of the
# GNU General Public License version 3 or any later version.

import os
import lockfile

from mozansible.stingray import StingrayConnection


def main():
    module = AnsibleModule(
        argument_spec = {
            'pool': {'required': True},
            'node': {'required': True},
            'state': {
                'required': False,
                'choices': ['active', 'disabled', 'draining'],
            },
            'url': {'required': True},
            'username': {'required': True},
            'password': {'required': True},
            'lockfile': {'required': False},
        },
    )

    url = module.params['url']
    username = module.params['username']
    password = module.params['password']
    pool = module.params['pool']
    node = module.params['node']
    state = module.params['state']

    lock = None
    if module.params['lockfile']:
        lockpath = os.path.join(os.environ['TMPDIR'], module.params['lockfile'])
        lock = lockfile.LockFile(lockpath)
        lock.acquire(60)

    try:
        conn = StingrayConnection(module, url, username, password)
        changed = conn.set_node_state(pool, node, state)
    finally:
        if lock:
            lock.release()

    module.exit_json(changed=changed, msg='Set %s state to %s' % (node, state))


from ansible.module_utils.basic import *
main()
