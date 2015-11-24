# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import hashlib
import logging
import os
import socket
import subprocess
import uuid

from batchreview import BatchReview
from ConfigParser import ConfigParser, NoSectionError, NoOptionError

from rbtools.api.client import RBClient

from kombu import (
    Connection,
    Exchange,
    Queue,
)


class MozReviewBot(object):

    def __init__(self, config_path=None, reviewboard_url=None,
                 reviewboard_user=None, reviewboard_password=None,
                 pulse_host=None, pulse_port=None, pulse_userid=None,
                 pulse_password=None, exchange=None, queue=None,
                 routing_key=None, pulse_timeout=None, pulse_ssl=False,
                 repo_root=None, logger=None):

        if logger is None:
            self.logger = logging.getLogger('mozreviewbot')
        else:
            self.logger = logger

        # We use options passed into __init__ preferentially. If any of these
        # are not specified, we next check the configuration file, if any.
        # Finally, we use environment variables.
        if config_path and not os.path.isfile(config_path):
            # ConfigParser doesn't seem to throw if it is unable to find the
            # config file so we'll explicitly check that it exists.
            self.logger.error('could not locate config file: %s' % (
                config_path))
            config_path = None
        if config_path:
            try:
                config = ConfigParser()
                config.read(config_path)
                reviewboard_url = (reviewboard_url
                                   or config.get('reviewboard', 'url'))
                reviewboard_user = (reviewboard_user
                                    or config.get('reviewboard', 'user'))
                reviewboard_password = (reviewboard_password
                                        or config.get('reviewboard',
                                                      'password'))
                pulse_host = pulse_host or config.get('pulse', 'host')
                pulse_port = pulse_port or config.get('pulse', 'port')
                pulse_userid = pulse_userid or config.get('pulse', 'userid')
                pulse_password = pulse_password or config.get('pulse',
                                                              'password')
                exchange = exchange or config.get('pulse', 'exchange')
                queue = queue or config.get('pulse', 'queue')
                routing_key = routing_key or config.get('pulse',
                                                        'routing_key')
                pulse_timeout = pulse_timeout or config.get('pulse',
                                                            'timeout')
                if pulse_ssl is None:
                    pulse_ssl = config.get('pulse', 'ssl')
            except NoSectionError as e:
                self.logger.error('configuration file missing section: %s' %
                                  e.section)
            try:
                repo_root = repo_root or config.get('hg', 'repo_root')
            except (NoOptionError, NoSectionError):
                # Subclasses do not need to define repo root if they do not
                # plan on using the hg functionality.
                pass

            # keep config around in case any subclasses would like to extract
            # options from it.
            self.config = config
        else:
            self.config = None

        reviewboard_url = reviewboard_url or os.environ.get('REVIEWBOARD_URL')
        pulse_host = pulse_host or os.environ.get('PULSE_HOST')
        pulse_port = pulse_port or os.environ.get('PULSE_PORT')

        self.rbclient = RBClient(reviewboard_url, username=reviewboard_user,
                                 password=reviewboard_password)
        self.api_root = self.rbclient.get_root()

        self.conn = Connection(hostname=pulse_host, port=pulse_port,
                               userid=pulse_userid, password=pulse_password,
                               ssl=pulse_ssl)

        self.exchange = Exchange(exchange, type='topic', durable=True)
        self.queue = Queue(name=queue, exchange=self.exchange, durable=True,
                           routing_key=routing_key, exclusive=False,
                           auto_delete=False)

        self.pulse_timeout = float(pulse_timeout)
        self.repo_root = repo_root

        self.hg = None
        for DIR in os.environ['PATH'].split(os.pathsep):
            p = os.path.join(DIR, 'hg')
            if os.path.exists(p):
                self.hg = p

    def _get_available_messages(self):
        messages = []

        def onmessage(body, message):
            messages.append((body, message))

        consumer = self.conn.Consumer([self.queue], callbacks=[onmessage],
                                      auto_declare=True)
        with consumer:
            try:
                self.conn.drain_events(timeout=self.pulse_timeout)
            except socket.timeout:
                pass

        return messages

    def _run_hg(self, hg_args):
        # TODO: Use hgtool.

        args = [self.hg] + hg_args

        env = dict(os.environ)
        env['HGENCODING'] = 'utf-8'

        null = open(os.devnull, 'w')

        # Execute at / to prevent Mercurial's path traversal logic from
        # kicking in and picking up unwanted config files.
        return subprocess.check_output(args, stdin=null, stderr=null,
                                       env=env, cwd='/')

    def ensure_hg_repo_exists(self, landing_repo_url, repo_url, pull_rev=None):
        # TODO: Use the root changeset in each repository as an identifier.
        #       This will enable "forks" to share the same local clone.
        #       The "share" extension now has support for this.
        #       Read hg help -e share for details about "pooled storage."
        #       We should probably deploy that.
        url = landing_repo_url or repo_url

        sha1 = hashlib.sha1(url).hexdigest()
        repo_path = os.path.join(self.repo_root, sha1)

        if not os.path.exists(repo_path):
            args = ['clone', url, repo_path]
            self.logger.debug('cloning %s' % url)
            self._run_hg(args)
            self.logger.debug('finished cloning %s' % url)

        args = ['-R', repo_path, 'pull', repo_url]

        if pull_rev:
            args.extend(['-r', pull_rev])

        self.logger.debug('pulling %s' % repo_url)
        self._run_hg(args)
        self.logger.debug('finished pulling %s' % repo_url)

        return repo_path

    def hg_commit_changes(self, repo_path, node, diff_context=None):
        """Obtain information about what changed in a Mercurial commit.

        The return value is a tuple of:

          (set(adds), set(dels), set(mods), None, diff)

        The first 4 items list what files changed in the changeset. The last
        item is a unified diff of the changeset.

        File copies are currently not returned. ``None`` is being used as a
        placeholder until support is needed.
        """
        part_delim = str(uuid.uuid4())
        item_delim = str(uuid.uuid4())

        parts = [
            '{join(file_adds, "%s")}' % item_delim,
            '{join(file_dels, "%s")}' % item_delim,
            '{join(file_mods, "%s")}' % item_delim,
            '{join(file_copies, "%s")}' % item_delim,
        ]

        template = part_delim.join(parts)

        self._run_hg(['-R', repo_path, 'up', '-C', node])

        res = self._run_hg(['-R', repo_path, 'log', '-r', node,
                            '-T', template])

        diff_args = ['-R', repo_path, 'diff', '-c', node]
        if diff_context is not None:
            diff_args.extend(['-U', str(diff_context)])
        diff = self._run_hg(diff_args)

        adds, dels, mods, copies = res.split(part_delim)
        adds = set(f for f in adds.split(item_delim) if f)
        dels = set(f for f in dels.split(item_delim) if f)
        mods = set(f for f in mods.split(item_delim) if f)
        # TODO parse the copies.

        return adds, dels, mods, None, diff

    def strip_nonpublic_changesets(self, repo_path):
        """Strip non-public changesets from a repository.

        Pulling changesets over and over results in many heads in a repository.
        This makes Mercurial slow. So, we prune non-public changesets/heads
        to keep repositories fast.
        """

        self._run_hg(['-R', repo_path, '--config', 'extensions.strip=',
                      'strip', '--no-backup', '-r', 'not public()'])

    def get_commit_files(self, commit):
        """Fetches a list of files that were changed by this commit."""

        rrid = commit['review_request_id']
        diff_revision = commit['diffset_revision']

        start = 0
        files = []
        while True:
            result = self.api_root.get_files(review_request_id=rrid,
                                             diff_revision=diff_revision,
                                             start=start)
            files.extend(result)
            start += result.num_items
            if result.num_items == 0 or start >= result.total_results:
                break
        return files

    def handle_available_messages(self):
        for body, message in self._get_available_messages():
            payload = body['payload']
            repo_url = payload['repository_url']
            landing_repo_url = payload['landing_repository_url']
            commits = payload['commits']
            # TODO: should we allow process commits to signal that we should
            #       skip acknowledging the message?
            try:
                for commit in commits:
                    rrid = commit['review_request_id']
                    diff_revision = commit['diffset_revision']

                    review = BatchReview(self.api_root, rrid, diff_revision)
                    self.process_commit(review, landing_repo_url, repo_url,
                                        commit)
            finally:
                # This prevents the queue from growing indefinitely but
                # prevents us from fixing whatever caused the exception
                # and restarting the bot to handle the message.
                message.ack()

    def listen_forever(self):
        while True:
            self.handle_available_messages()

    def process_commit(self, review, repo_url, commits):
        pass
