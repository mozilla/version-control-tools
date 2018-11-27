# Copyright 2017 Octobus <contact@octobus.net>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.
"""help dealing with code source reformating

The extension provides a way to run code-formatting tools in a way that avoids
conflicts related to this formatting when merging/rebasing code across the
reformatting.

A new `format-source` command is provided, to apply code formatting tool on
some specific files. This information is recorded into the repository and
reused when merging. The client doing the merge needs the extension for this
logic to kick in.

Code formatting tools have to be registered in the configuration. The tool
"name" will be used to identify a specific command accross all repositories.
It is mapped to a command line that must output the formatted content on its
standard output.

For each tool a list of files affecting the result of the formatting can be
configured with the "configpaths" suboption, which is read and registered at
"hg format-source" time.  Any change in those files should trigger
reformatting.

Example::

    [format-source]
    json = python -m json.tool
    clang = clang-format -style=Mozilla
    clang:configpaths = .clang-format, .clang-format-ignore

We do not support specifying the mapping of tool name to tool command in the
repository itself for security reasons.

The code formatting information is tracked in a .hg-format-source file at the
root of the repository.

Warning: There is no special logic handling renames so moving files to a
directory not covered by the patterns used for the initial formatting will
likely fail.
"""

from __future__ import absolute_import
import os
import json
import tempfile

from mercurial import (
    commands,
    cmdutil,
    encoding,
    error,
    extensions,
    filemerge,
    match,
    merge,
    registrar,
    scmutil,
    util,
    worker,
)

from mercurial.i18n import _

__version__ = '0.1.0.dev'
testedwith = '4.4.2 4.5.3 4.6.2 4.7.2 4.8'
minimumhgversion = '4.4'

cmdtable = {}

if util.safehasattr(registrar, 'command'):
    command = registrar.command(cmdtable)
else: # compat with hg < 4.3
    command = cmdutil.command(cmdtable)

if util.safehasattr(registrar, 'configitem'):
    # where available, register our config items
    configtable = {}
    configitem = registrar.configitem(configtable)
    configitem('format-source', '.*', default=None, generic=True)

file_storage_path = '.hg-format-source'

@command('format-source',
        [] + commands.walkopts + commands.commitopts + commands.commitopts2,
        _('TOOL FILES+'))
def cmd_format_source(ui, repo, tool, *pats, **opts):
    """format source file using a registered tools

    This command run TOOL on FILES and record this information in a commit to
    help with future merge.

    The actual command run for TOOL needs to be registered in the config. See
    :hg:`help -e formatsource` for details.
    """
    if repo.getcwd():
        msg = _("format-source must be run from repository root")
        hint = _("cd %s") % repo.root
        raise error.Abort(msg, hint=hint)

    if not pats:
        raise error.Abort(_('no files specified'))

    # XXX We support glob pattern only for now, the recursive behavior of various others is a bit wonky.
    for pattern in pats:
        if not pattern.startswith('glob:'):
            msg = _("format-source only supports explicit 'glob' patterns "
                    "for now ('%s')")
            msg %= pattern
            hint = _('maybe try with "glob:%s"') % pattern
            raise error.Abort(msg, hint=hint)

    # lock the repo to make sure no content is changed
    with repo.wlock():
        # formating tool
        if ' ' in tool:
            raise error.Abort(_("tool name cannot contain space: '%s'") % tool)
        shell_tool = repo.ui.config('format-source', tool)
        tool_config_files = repo.ui.configlist('format-source', '%s:configpaths' % tool)
        file_ext = tuple(repo.ui.configlist('format-source', '%s:fileext' % tool))
        if not shell_tool:
            msg = _("unknown format tool: %s (no 'format-source.%s' config)")
            raise error.Abort(msg.format(tool, tool))
        if not file_ext:
            msg = _("no {}:fileext present".format(tool))
            raise error.Abort(msg.format(tool, tool))
        cmdutil.bailifchanged(repo)
        cmdutil.checkunfinished(repo, commit=True)
        wctx = repo[None]
        # files to be formatted
        matcher = scmutil.match(wctx, pats, opts)
        files = list(wctx.matches(matcher))

        batchformat(repo, wctx, tool, shell_tool, file_ext, files)

        # update the storage to mark formated file as formatted
        with repo.wvfs(file_storage_path, mode='ab') as storage:
            for pattern in pats:
                # XXX if pattern was relative, we need to reroot it from the
                # repository root. For now we constrainted the command to run
                # at the root of the repository.
                data = {'tool': encoding.unifromlocal(tool),
                        'pattern': encoding.unifromlocal(pattern)}
                if tool_config_files:
                    data['configpaths'] = [encoding.unifromlocal(path)
                                           for path in tool_config_files]
                entry = json.dumps(data, sort_keys=True)
                assert '\n' not in entry
                storage.write('%s\n' % entry)

        if file_storage_path not in wctx:
            storage_matcher = scmutil.match(wctx, ['path:' + file_storage_path])
            cmdutil.add(ui, repo, storage_matcher, '', True)

        # commit the whole
        with repo.lock():
            commit_patterns = ['path:' + file_storage_path]
            commit_patterns.extend(pats)
            return commands._docommit(ui, repo, *commit_patterns, **opts)

def batchformat(repo, wctx, tool, shell_tool, file_ext, files):
    for filepath in files:
        if not filepath.endswith(tuple(file_ext)):
            continue
        flags = wctx.flags(filepath)
        if 'l' in flags:
            # links should just be skipped
            repo.ui.warn(_('Skipping symlink, %s\n') % filepath)
            continue
        newcontent = run_tools(repo.ui, repo.root, tool, shell_tool, filepath, filepath)
        # if the formating tool returned an empty string then do not write it
        if len(newcontent):
            # XXX we could do the whole commit in memory
            with repo.wvfs(filepath, 'wb') as formatted_file:
                formatted_file.write(newcontent)
            wctx.filectx(filepath).setflags(False, 'x' in flags)

def run_tools(ui, root, tool, cmd, filepath, filename):
    """Run the a formatter tool on a specific file"""
    env = encoding.environ.copy()
    env['HG_FILENAME'] = filename
    # XXX escape special character in filepath
    format_cmd = "%s %s" % (cmd, filepath)
    ui.debug('running %s\n' % format_cmd)
    ui.pushbuffer(subproc=True)
    try:
        ui.system(format_cmd,
                  environ=env,
                  cwd=root,
                  onerr=error.Abort,
                  errprefix=tool)
    finally:
        newcontent = ui.popbuffer()
    return newcontent

def touched(repo, old_ctx, new_ctx, paths):
    matcher = rootedmatch(repo, new_ctx, paths)
    if any(path in new_ctx for path in paths):
        status = old_ctx.status(other=new_ctx, match=matcher)
        return bool(status.modified or status.added)
    return False

def formatted(repo, old_ctx, new_ctx):
    """retrieve the list of formatted patterns between <old> and <new>

    return a {'tool': [patterns]} mapping
    """
    new_formatting = {}
    if touched(repo, old_ctx, new_ctx, [file_storage_path]):
        # quick and dirty line diffing
        # (the file is append only by contract)

        new_lines = set(new_ctx[file_storage_path].data().splitlines())
        old_lines = set()
        if file_storage_path in old_ctx:
            old_lines = set(old_ctx[file_storage_path].data().splitlines())
        new_lines -= old_lines
        for line in new_lines:
            entry = json.loads(line)
            def getkey(key):
                return encoding.unitolocal(entry[key])
            new_formatting.setdefault(getkey('tool'), set()).add(getkey('pattern'))
    if file_storage_path in old_ctx:
        for line in old_ctx[file_storage_path].data().splitlines():
            entry = json.loads(line)
            if not entry.get('configpaths'):
                continue
            configpaths = [encoding.unitolocal(path) for path in entry['configpaths']]
            def getkey(key):
                return encoding.unitolocal(entry[key])
            if touched(repo, old_ctx, new_ctx, configpaths):
                new_formatting.setdefault(getkey('tool'), set()).add(getkey('pattern'))
    return new_formatting

def allformatted(repo, local, other, ancestor):
    """return a mapping of formatting needed for all involved changeset
    """

    cachekey = (local.node, other.node(), ancestor.node())
    cached = getattr(repo, '_formatting_cache', {}).get(cachekey)

    if cached is not None:
        return cached

    local_formating = formatted(repo, ancestor, local)
    other_formating = formatted(repo, ancestor, other)
    full_formating = local_formating.copy()
    for key, value in other_formating.iteritems():
        if key in local_formating:
            value = value | local_formating[key]
        full_formating[key] = value

    all = [
        (local, local_formating),
        (other, other_formating),
        (ancestor, full_formating)
    ]
    for ctx, formatting in all:
        for tool, patterns in formatting.iteritems():
            formatting[tool] = rootedmatch(repo, ctx, patterns)

    final = tuple(formatting for __, formatting in all)
    getattr(repo, '_formatting_cache', {})[cachekey] = cached

    return final

def rootedmatch(repo, ctx, patterns):
    """match patterns agains the root of a repository"""
    # rework of basectx.match to ignore current working directory

    # Only a case insensitive filesystem needs magic to translate user input
    # to actual case in the filesystem.
    icasefs = not util.fscasesensitive(repo.root)
    if util.safehasattr(match, 'icasefsmatcher'): #< hg 4.3
        if icasefs:
            return match.icasefsmatcher(repo.root, repo.root, patterns,
                                        default='glob', auditor=repo.auditor,
                                        ctx=ctx)
        else:
            return match.match(repo.root, repo.root, patterns, default='glob',
                               auditor=repo.auditor, ctx=ctx)
    else:
        return match.match(repo.root, repo.root, patterns, default='glob',
                           auditor=repo.auditor, ctx=ctx, icasefs=icasefs)

def apply_formating(repo, formatting, fctx):
    """apply formatting to a file context (if applicable)"""
    data = None
    for tool, matcher in sorted(formatting.items()):
        # matches?
        if matcher(fctx.path()):
            if data is None:
                data = fctx.data()
            shell_tool = repo.ui.config('format-source', tool)
            if not shell_tool:
                msg = _("format-source, no command defined for '%s',"
                        " skipping formating: '%s'\n")
                msg %= (tool, fctx.path())
                repo.ui.warn(msg)
                continue
            _, file_ext = os.path.splitext(fctx.path())
            with tempfile.NamedTemporaryFile(delete=True, suffix=file_ext if file_ext else "", mode='wb') as f:
                f.write(data)
                f.flush()
                data = run_tools(repo.ui, repo.root, tool,
                                 shell_tool, f.name, fctx.path())
    if data is not None:
        fctx.data = lambda: data


def wrap_filemerge44(origfunc, premerge, repo, wctx, mynode, orig, fcd, fco, fca,
                   *args, **kwargs):
    """wrap the file merge logic to apply formatting on files that needs them"""
    _update_filemerge_content(repo, fcd, fco, fca)
    return origfunc(premerge, repo, wctx, mynode, orig, fcd, fco, fca,
                    *args, **kwargs)

def wrap_filemerge43(origfunc, premerge, repo, mynode, orig, fcd, fco, fca,
                   *args, **kwargs):
    """wrap the file merge logic to apply formatting on files that needs them"""
    _update_filemerge_content(repo, fcd, fco, fca)
    return origfunc(premerge, repo, mynode, orig, fcd, fco, fca,
                    *args, **kwargs)

def _update_filemerge_content(repo, fcd, fco, fca):
    if fcd.isabsent() or fco.isabsent() or fca.isabsent():
        return
    local = fcd._changectx
    other = fco._changectx
    ances = fca._changectx
    all = allformatted(repo, local, other, ances)
    local_formating, other_formating, full_formating = all
    apply_formating(repo, local_formating, fco)
    apply_formating(repo, other_formating, fcd)
    apply_formating(repo, full_formating, fca)

    if 'data' in vars(fcd): # XXX hacky way to check if data overwritten
        file_path = repo.wvfs.join(fcd.path())
        with open(file_path, 'wb') as local_file:
            local_file.write(fcd.data())

def wrap_update(orig, repo, *args, **kwargs):
    """install the formatting cache"""
    repo._formatting_cache = {}
    try:
        return orig(repo, *args, **kwargs)
    finally:
        del repo._formatting_cache

def uisetup(self):
    pre44hg = filemerge._filemerge.__code__.co_argcount < 9
    if pre44hg:
        extensions.wrapfunction(filemerge, '_filemerge', wrap_filemerge43)
    else:
        extensions.wrapfunction(filemerge, '_filemerge', wrap_filemerge44)
    extensions.wrapfunction(merge, 'update', wrap_update)
