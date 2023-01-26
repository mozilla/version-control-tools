#!/usr/bin/env python

TRY_SYNTAX_MISSING = b"""
Your push does not specify any jobs to run on try. You can still
schedule jobs by selecting the drop down at the top right of your
push in treeherder and choosing 'Add new Jobs'.

For more information, see https://wiki.mozilla.org/Try.
"""

TRY_JOBS_MISSING = b"""
Your try syntax would not trigger any jobs. Either specify a build
with '-p' or an arbitrary job with '-j'. If you intended to push
without triggering any jobs, omit the try syntax completely.

For more information, see https://wiki.mozilla.org/Try.
"""


def print_banner(ui, level, message):
    width = max(len(l) for l in message.splitlines())
    banner = [
        (b" %s " % level.upper()).center(width, b"*"),
        message.strip(),
        b"*" * width,
    ]
    ui.write(b"\n" + b"\n".join(banner) + b"\n\n")


def hook(ui, repo, source=None, **kwargs):
    if source in (b"pull", b"strip"):
        return 0

    tip = repo[b"tip"]
    comment = tip.description()
    config_found = b"try_task_config.json" in tip.manifest()
    syntax_found = b"try:" in comment
    if not config_found and not syntax_found:
        print_banner(ui, b"warning", TRY_SYNTAX_MISSING)
    elif syntax_found and b"-p none" in comment and b"-j" not in comment:
        print_banner(ui, b"error", TRY_JOBS_MISSING)
        return 1
    return 0
