from __future__ import absolute_import, unicode_literals

import os.path
import os
import unittest

from betamax import Betamax
from betamax_serializers import pretty_json
import github3

from mozvcssync.github_pr import GitHubPR

HERE = os.path.abspath(os.path.dirname(__file__))
AUTH_TOKEN = os.environ.get('GH_AUTH_TOKEN', 'x' * 20)


Betamax.register_serializer(pretty_json.PrettyJSONSerializer)
with Betamax.configure() as config:
    config.cassette_library_dir = os.path.join(HERE, 'cassettes')
    config.default_cassette_options['serialize_with'] = 'prettyjson'
    config.define_cassette_placeholder(b'<AUTH_TOKEN>', AUTH_TOKEN)
    config.default_cassette_options['record_mode'] = os.environ.get(
        'BETMAX_RECORD_MODE', 'once')


class TestGithubPR(unittest.TestCase):
    def setUp(self):
        self.github = github3.GitHub()
        self.session = self.github._session
        self.configure_session(self.session)
        self.recorder = Betamax(self.session)
        with self.recorder.use_cassette('github-pr-initialization'):
            self.ghpr = GitHubPR(
                AUTH_TOKEN, 'servo/servo', '', github=self.github)

    def configure_session(self, session):
        """Configure a requests session for testing."""
        session.headers.update({'Accept-Encoding': 'identity'})

    def test_upstream_repo_missing(self):
        self.ghpr.upstream_user = "auserwhichdoesntexist"
        self.ghpr.repo_name = "arepowhichdoesntexist"

        with self.recorder.use_cassette('github-pr-upstream-no-repo'):
            with self.assertRaises(Exception) as context:
                self.ghpr.upstream_repo()

        self.assertTrue(
            b'failed to find github repo' in str(context.exception))

    def test_upstream_repo_exists(self):
        with self.recorder.use_cassette('github-pr-upstream-repo'):
            upstream = self.ghpr.upstream_repo()

        assert upstream.full_name == 'servo/servo'
