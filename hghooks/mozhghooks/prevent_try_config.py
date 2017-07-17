#!/usr/bin/env python

TRY_CONFIG_FOUND = """
You are trying to commit the temporary 'try_task_config.json' file
on a non-try branch. Either make sure you are pushing to try or
remove the file and push again.
"""


def print_banner(ui, level, message):
    width = max(len(l) for l in message.splitlines())
    banner = [
        ' {} '.format(level.upper()).center(width, '*'),
        message.strip(),
        '*' * width,
    ]
    ui.write('\n' + '\n'.join(banner) + '\n\n')


def hook(ui, repo, node, source=None, **kwargs):
    if source in ('pull', 'strip'):
        return 0

    for rev in repo.changelog.revs(repo[node].rev()):
        ctx = repo[rev]
        if 'try_task_config.json' in ctx.files():
            print_banner(ui, 'error', TRY_CONFIG_FOUND)
            return 1

    return 0
