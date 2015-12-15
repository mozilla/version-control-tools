# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import argparse
import json
import logging
import os
import random
import subprocess
import sys
import tempfile


from mozreviewbotlib import MozReviewBot


EXTENSIONS = ['.js', '.jsm', '.jsx']


# Any repositories hoping to use ESLintBot should have a ESLINT_CONFIG
# file in the root repository folder.
ESLINT_CONFIG = '.eslintrc'


class ESLintBot(MozReviewBot):
    """This bot runs ESLint against JavaScript files under review"""

    def process_commit(self, review, landing_repo_url, repo_url, commit):
        revision = commit['rev']

        self.logger.info('reviewing revision: %s (review request: %d)' %
                         (revision[:12], commit['review_request_id']))

        repo_path = self.ensure_hg_repo_exists(landing_repo_url, repo_url,
                                               revision)

        if not os.path.isfile(os.path.join(repo_path, ESLINT_CONFIG)):
            self.logger.info('Not reviewing revision: %s no %s file in '
                             'repository root folder'
                             % (revision, ESLINT_CONFIG))
            return

        adds, dels, mods, copies, diff = self.hg_commit_changes(repo_path,
                                                                revision,
                                                                diff_context=0)

        rel_adds = set(f for f in adds if os.path.splitext(f)[1] in EXTENSIONS)
        rel_mods = set(f for f in mods if os.path.splitext(f)[1] in EXTENSIONS)
        relevant = rel_adds | rel_mods

        if not relevant:
            self.logger.info('not reviewing revision: %s no relevant '
                             'Javascript changes in commit' % revision)
            return

        oldcwd = os.getcwd()
        try:
            os.chdir(repo_path)

            # Unfortunately, running ./mach eslint will result in a bunch of
            # mach logging going into stdout, which we don't care about. We
            # work around this by outputting the ESLint output to a temporary
            # file which we'll read in from. Note that this will only work
            # on UNIX-like systems.
            output_file = tempfile.NamedTemporaryFile().name

            args = [
                './mach',
                'eslint',
                '--format=json',
                ('--output-file=%s' % output_file)
            ] + list(relevant)

            subprocess.check_output(args)
            with open(output_file, 'r') as f:
                results = json.load(f)
                path = os.path.abspath(f.name)

            os.remove(path)
        finally:
            os.chdir(oldcwd)

        error_count = 0
        # The join assures we get a trailing slash
        base_path = os.path.join(os.path.dirname(repo_path), revision, '')

        for result in results:
            if not result['errorCount'] and not result['warningCount']:
                continue

            error_count += result['errorCount'] + result['warningCount']
            # Do some awful hacks to get a repo-relative file path:
            file_path = os.path.abspath(result['filePath'])
            file_path = file_path[len(base_path):]

            for message in result['messages']:
                if message['severity'] == 1:
                    severity = "Warning"
                else:
                    severity = "Error"

                comment = '%s - %s' % (severity, message['message'])

                if 'column' in message:
                    comment += " (column %s)" % message['column']

                line = 0
                if 'line' in message:
                    line = message['line']

                review.comment(file_path, line, 1, comment)

        commentlines = []

        if error_count:
            commentlines.extend([
                'I analyzed your JS changes and found %d errors.' % (
                    error_count),
            ])
        else:
            commentlines.extend([
                'Congratulations, there were no JS static analysis '
                'issues with this patch!',
            ])

        commentlines.extend([
            '',
            'The following files were examined:',
            '',
        ])
        commentlines.extend('  %s' % f for f in sorted(relevant))

        review.publish(body_top='\n'.join(commentlines),
                       ship_it=error_count == 0)

        self.strip_nonpublic_changesets(repo_path)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--config-path',
                        help='Path to configuration file for bot options')
    parser.add_argument('--forever', action='store_true',
                        help='Run the bot in an endless loop')
    parser.add_argument('--log-level', default='INFO',
                        help='Log level at which to log events')
    args = parser.parse_args()

    logging.basicConfig(level=getattr(logging, args.log_level.upper()),
                        stream=sys.stdout)

    bot = ESLintBot(config_path=args.config_path)
    if args.forever:
        bot.listen_forever()
    else:
        bot.handle_available_messages()
