#!/usr/bin/env python

TRY_SYNTAX_MISSING = """
Your push does not specify any jobs to run on try. You can still
schedule jobs by selecting the drop down at the top right of your
push in treeherder and choosing 'Add new Jobs'.

For more information, see https://wiki.mozilla.org/Try.
"""

TRY_JOBS_MISSING = """
Your try syntax would not trigger any jobs. Either specify a build
with '-p' or an arbitrary job with '-j'. If you intended to push
without triggering any jobs, omit the try syntax completely.

For more information, see https://wiki.mozilla.org/Try.
"""


def print_banner(ui, level, message):
    width = max(len(l) for l in message.splitlines())
    banner = [
        ' {} '.format(level.upper()).center(width, '*'),
        message.strip(),
        '*' * width,
    ]
    ui.write('\n' + '\n'.join(banner) + '\n\n')


def hook(ui, repo, source=None, **kwargs):
    if source in ('pull', 'strip'):
        return 0

    tip = repo.changectx('tip')
    comment = tip.description()
    config_found = 'try_task_config.json' in tip.manifest()
    syntax_found = 'try:' in comment
    if not config_found and not syntax_found:
        print_banner(ui, 'warning', TRY_SYNTAX_MISSING)
    elif syntax_found and "-p none" in comment and "-j" not in comment:
        print_banner(ui, 'error', TRY_JOBS_MISSING)
        return 1
    return 0
