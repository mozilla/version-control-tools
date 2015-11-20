# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import argparse
import logging
import os
import random
import sys

from flake8.engine import get_style_guide
from mozreviewbotlib import MozReviewBot
from pep8 import (
    DiffReport,
    parse_udiff
)


# Maps a flake8 error code to a tuple of (start_line_offset, num_lines)
LINE_ADJUSTMENTS = {
    # continuation line under-indented for hanging indent
    'E121': (-1, 2),
    # continuation line missing indentation or outdented
    'E122': (-1, 2),
    # continuation line over-indented for hanging indent
    'E126': (-1, 2),
    # continuation line over-indented for visual indent
    'E127': (-1, 2),
    # continuation line under-indented for visual indent
    'E128': (-1, 2),
    # continuation line unaligned for hanging indend
    'E131': (-1, 2),
    # expected 1 blank line, found 0
    'E301': (-1, 2),
    # expected 2 blank lines, found 1
    'E302': (-2, 3),
}

NO_ERRORS_QUIPS = [
    'And now for something completely different.',
]

ERRORS_QUIPS = [
    'Always look on the bright side of life.',
]


def _cmp_errors(a, b):
    """Comparison function for 2 pep8 error tuples.

    We sort first by line number then by error code.
    """
    aline, aoffset, acode, atext, adoc = a
    bline, boffset, bcode, btext, bdoc = b

    if aline < bline:
        return -1
    elif aline > bline:
        return 1

    if aoffset < boffset:
        return -1
    elif aoffset > boffset:
        return 1

    if acode < bcode:
        return -1
    elif acode > bcode:
        return 1

    return 0


class CapturingDiffReport(DiffReport):
    """A custom pep8 report that buffers results to a data structure.

    Existing report classes print output. We are headless. We store the results
    for later processing.
    """
    def __init__(self, options):
        super(CapturingDiffReport, self).__init__(options)

        self.file_results = {}

    def get_file_results(self):
        self.file_results[self.filename] = self._deferred_print
        return self.file_errors


class PylintBot(MozReviewBot):
    """This bot runs flake8 against python files under review"""

    def process_commit(self, review, landing_repo_url, repo_url, commit):
        revision = commit['rev']

        self.logger.info('reviewing revision: %s (review request: %d)' %
                         (revision[:12], commit['review_request_id']))

        repo_path = self.ensure_hg_repo_exists(landing_repo_url, repo_url,
                                               revision)

        self.hg_commit_changes(repo_path, revision, diff_context=0)

        adds, dels, mods, copies, diff = self.hg_commit_changes(repo_path,
                                                                revision,
                                                                diff_context=0)

        rel_adds = set(f for f in adds if f.endswith('.py'))
        rel_mods = set(f for f in mods if f.endswith('.py'))
        relevant = rel_adds | rel_mods

        if not relevant:
            self.logger.info('not reviewing revision: %s no relevant '
                             'python changes in commit' % revision)
            return

        # flake8's multiprocessing default doesn't work synchronously for
        # some reason. Probably because our saved state isn't being
        # transferred across process boundaries. Specify jobs=0 to get
        # results.
        style = get_style_guide(parse_argv=False, jobs=0)
        style.options.selected_lines = {}
        for k, v in parse_udiff(diff).items():
            if k.startswith('./'):
                k = k[2:]
                style.options.selected_lines[k] = v
        style.options.report = CapturingDiffReport(style.options)

        oldcwd = os.getcwd()
        try:
            os.chdir(repo_path)
            results = style.check_files(relevant)
        finally:
            os.chdir(oldcwd)

        error_count = 0
        for filename, errors in sorted(results.file_results.items()):
            if not errors:
                continue

            errors = sorted(errors, cmp=_cmp_errors)

            for line, offset, code, text, doc in errors:
                error_count += 1
                num_lines = 1
                comment = '%s: %s' % (code, text)

                if code in LINE_ADJUSTMENTS:
                    line_offset, num_lines = LINE_ADJUSTMENTS[code]
                    line += line_offset

                review.comment(filename, line, num_lines, comment)

        commentlines = []

        if error_count:
            commentlines.extend([
                random.choice(ERRORS_QUIPS),
                '',
                'I analyzed your Python changes and found %d errors.' % (
                    error_count),
            ])
        else:
            commentlines.extend([
                random.choice(NO_ERRORS_QUIPS),
                '',
                'Congratulations, there were no Python static analysis '
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

    bot = PylintBot(config_path=args.config_path)
    if args.forever:
        bot.listen_forever()
    else:
        bot.handle_available_messages()
