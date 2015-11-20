# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from mozreviewbotlib import MozReviewBot


class SnarkBot(MozReviewBot):
    """This implements a simple review bot.

       It can be used as a basis for creating more sophisticated reviewers.
       It is also used to test the MozReviewBot base class.
    """

    def __init__(self, snark, *args, **kwargs):
        super(SnarkBot, self).__init__(*args, **kwargs)
        self.snark = snark

    def process_commit(self, review, landing_repo_url, repo_url, commit):
        """This is called for each group of commits that is found on Pulse.

           It can also be called directly to facillitate testing. The repo_url
           is the URL for the underlying review repository. The commit is a
           dictionary containing commits to review, e.g.

                commit = {'review_request_id': 42,
                          'diffset_revision': 1,
                          'commit': 'aaaaaaaaaaaa'}
        """

        # We fetch the files that were changed in this commit. This list
        # could be filtered so we only look at certain file types before
        # we continue.
        files = self.get_commit_files(commit)

        self.logger.info('reviewing commit: %s for review request: %d '
                         'diff_revision: %d' % (commit['rev'][:12],
                                                commit['review_request_id'],
                                                commit['diffset_revision']))
        for f in files:
            self.logger.info('looking at file: %s (%s)' % (f.source_file,
                                                           f.dest_file))

            changed_lines = review.changed_lines_for_file(f.dest_file)

            # We then fetch the patched file.
            pf = f.get_patched_file()
            code = pf.rsp['resource']['data']

            # In this case we just log the text, but this is where the bot
            # would analyze the patch.
            self.logger.info(code)

            # We create a comment on one of the changed lines in the file
            review.comment(f.dest_file, changed_lines.pop(), 1, self.snark,
                           True)

        review.publish(body_top='This is what I think of your changes:',
                       ship_it=False)


if __name__ == '__main__':
    import argparse
    import logging
    import sys

    parser = argparse.ArgumentParser()

    parser.add_argument('--config-path',
                        help='Path to configuration file for bot options')
    parser.add_argument('--log-level', default='INFO',
                        help='Log level at which to log events')
    parser.add_argument('--snark', default='seriously?',
                        help='Snarky comment to use for reviews')

    args = parser.parse_args()

    logging.basicConfig(level=getattr(logging, args.log_level.upper()),
                        stream=sys.stdout)

    snark = SnarkBot(args.snark, config_path=args.config_path)

    # This will drain all available messages on Pulse and call process_commits
    # for the commits associated with each message. Use listen_forever() to
    # process messages in a endless loop.
    snark.handle_available_messages()
