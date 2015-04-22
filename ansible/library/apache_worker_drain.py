#!/usr/bin/env python
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

import requests
import time


DOCUMENTATION = '''
---
module: apache_worker_drain
short_description: Waits for Apache workers to drain
description:
     - When doing a rolling update, you often want to wait for active requests
       and connections to drain. Ansible's built-in wait_for module can look
       for TCP connections. However, it counts TIME_WAIT as an active
       connection, which adds significant wait times during rolling updates.
       Waiting for Apache workers to flush is accurate and faster.
    - This module polls Apache's server-status and waits for the worker count
      to reach 1. The count never reaches 0, as the request to server-status
      occupies a worker slot.
options:
  url:
    description:
      - URL for Apache server-status. "?auto" is added automatically.
    default: http://localhost/server-status
  timeout:
    description:
      - How long to wait for worker count to drain
    default: 300
'''

def get_busy_workers(url):
    res = requests.get(url, timeout=5)
    for line in res.text.splitlines():
        k, v = line.split(': ', 1)

        if k != 'BusyWorkers':
            continue

        return int(v)

    return None


def main():
    module = AnsibleModule(
        argument_spec = {
            'url': {'default': 'http://localhost/server-status'},
            'timeout': {'default': 300},
        },
    )

    url = module.params['url']
    timeout = int(module.params['timeout'])

    if not url.endswith('?auto'):
        url += '?auto'

    end = time.time() + timeout
    drained = False
    count = 0
    while time.time() < end:
        try:
            count += 1
            busy = get_busy_workers(url)
            if busy == 1:
                drained = True
                break

            time.sleep(1)

        except Exception as e:
            module.fail_json(msg='HTTP request to %s failed: %s' % (url, e))

    if drained:
        module.exit_json(changed=True, state='drained', poll_count=count)
    else:
        module.fail_json(msg='Timeout when waiting for server to drain')


from ansible.module_utils.basic import *
main()
