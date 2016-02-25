#!/usr/bin/env python

TRY_SYNTAX_MISSING = """
Your push does not contain any try syntax, so no jobs will be
scheduled automatically. If this was intentional, you can still
schedule jobs by selecting the drop down at the top right of your
push in treeherder and choosing 'Add new Jobs'.

If you meant to schedule jobs, remember the try syntax must
appear in the *last* commit of your push. For assistance with try
server, see https://wiki.mozilla.org/Try.
"""

TRY_JOBS_MISSING = """
Your try syntax would not trigger any jobs. Either specify a build
with '-p' or an arbitrary job with '-j'. If you intended to push
without triggering any jobs, omit the try syntax completely. For
assistance with try server, see https://wiki.mozilla.org/Try.
"""


def print_banner(level, message):
    width = max(len(l) for l in message.splitlines())
    banner = [
        ' {} '.format(level.upper()).center(width, '*'),
        message.strip(),
        '*' * width,
    ]
    print('\n' + '\n'.join(banner) + '\n')


def hook(ui, repo, source=None, **kwargs):
    if source in ('pull', 'strip'):
        return 0

    # Block the push unless they use the try_syntax
    # 'try: ' is enough to activate try_parser and get the default set
    comment = repo.changectx('tip').description()
    if "try: " not in comment:
        print_banner('warning', TRY_SYNTAX_MISSING)
    elif "-p none" in comment and "-j" not in comment:
        print_banner('error', TRY_JOBS_MISSING)
        return 1
    return 0
