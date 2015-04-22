# This software may be used and distributed according to the terms of the
# GNU General Public License version 3 or any later version.

import requests


class StingrayConnection(object):
    """Represents a connection to a Stringray Traffic Manager."""

    def __init__(self, module, url, username, password):
        self.module = module
        self.session = requests.Session()
        self.session.auth = (username, password)
        # TODO plug in SSL verification
        self.session.verify = False
        self._url = '%s/api/tm/3.2' % url.rstrip('/')

    def request(self, path, method='GET', **kwargs):
        response = self.session.request(
                method,
                '%s/%s' % (self._url, path.lstrip('/')),
                **kwargs)

        if response.status_code == 404:
            return None

        j = response.json()
        if 'error_text' in j:
            self.module.fail_json(
                    msg='Error talking to Stingray: %s' % j['error_text'])

        return j

    def get_pool_state(self, pool):
        state = self.request('config/active/pools/%s' % pool)

        if not state:
            self.module.fail_json(msg='Pool %s not found' % pool)

        return state

    def set_node_state(self, pool, node, state):
        """Set the state of a node in a pool.

        This is used to mark a node active, disabled, or draining.

        This will error if the pool or node is not known.

        Returns a boolean indicating whether anything changed.
        """
        pool_state = self.get_pool_state(pool)

        nodes = []
        found = False
        for n in pool_state['properties']['basic']['nodes_table']:
            if n['node'] == node:
                if n['state'] == state:
                    return False

                found = True
                n['state'] = state

            nodes.append(n)

        if not found:
            self.module.fail_json(msg='Node %s not found in pool %s' % (
                node, pool))

        new_state = {'properties': {'basic': {'nodes_table': nodes}}}

        self.request('config/active/pools/%s' % pool, method='PUT',
                     json=new_state)

        return True
