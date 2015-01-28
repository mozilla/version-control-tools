import gzip
import json
import mock
import os
import unittest
import responses
import sys

sys.path.insert(0, os.path.join(os.path.split(os.path.split(
                os.path.realpath(__file__))[0])[0], 'autoland'))
import autoland_pulse


class TestAutolandPulse(unittest.TestCase):

    @responses.activate
    def test_autoland_messages(self):

        def is_known_testrun(dbconn, tree, rev):
            return (tree == 'try'
                    and rev == '7dda5def66faf5d9d0173aed32d33c964247daf3')

        autoland_pulse.is_known_testrun = is_known_testrun

        # set up responses for selfserve.jobs_for_revision
        with open('test-data/selfserve-jobs-for-revision.html') as f:
            jobs_for_revision = f.read()
        responses.add(responses.GET,
                      ('https://secure.pub.build.mozilla.org/buildapi/'
                       'self-serve/try/rev/'
                       '7dda5def66faf5d9d0173aed32d33c964247daf3'),
                      body=jobs_for_revision, status=200,
                      content_type='application/json', match_querystring=True)
        responses.add(responses.GET,
                      ('https://secure.pub.build.mozilla.org/buildapi/'
                       'self-serve/try/rev/7dda5def66fa'),
                      body=jobs_for_revision, status=200,
                      content_type='application/json', match_querystring=True)

        # read and replay canned messages
        with gzip.open('test-data/pulse-messages.json.gz') as f:
            message_data = json.load(f)

        hit_monitored_testrun = False
        for i, data in enumerate(message_data):
            autoland_pulse.dbconn = mock.Mock()
            autoland_pulse.logger = mock.Mock()
            message = mock.Mock()

            autoland_pulse.handle_message(data, message)
            self.assertTrue(message.ack.called)

            tree, rev = autoland_pulse.extract_tree_and_rev(data['payload'])

            if (tree == 'try' and
                    rev == '7dda5def66faf5d9d0173aed32d33c964247daf3'):

                hit_monitored_testrun = True
                self.assertTrue(autoland_pulse.logger.info.called)
                self.assertEqual(autoland_pulse.logger.info.call_args[0][0],
                                 'pending: 0 running: 0 builds: 4')
            else:
                self.assertFalse(autoland_pulse.logger.info.called)

        self.assertTrue(hit_monitored_testrun)

if __name__ == '__main__':
    unittest.main()
