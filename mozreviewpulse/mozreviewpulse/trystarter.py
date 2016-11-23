# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import taskcluster


class TryStarter:
    """Reads 'review request posted' events from pulse and starts Try jobs
    on TaskCluster for the review requests' changset.
    """

    def __init__(self, queue, taskcluster_url, confirm_connections=True):
        self.queue = queue
        self.taskcluster_url = taskcluster_url

        if confirm_connections:
            self._ensure_taskcluster_connection(taskcluster_url)

    def get(self):
        """Return a single message from the Pulse service."""
        return self.queue.get()

    def _ensure_taskcluster_connection(self, taskcluster_url):
        index = taskcluster.Index(options={'baseUrl': taskcluster_url})
        # This will raise a subclass of TaskclusterFailure if things go wrong.
        index.ping()

    def process_messages(self):
        """Process all Pulse messages and dispatch Try requests for them."""
        pass