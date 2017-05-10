# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import, unicode_literals

import hashlib
import logging
import os
import subprocess
import tempfile

import dulwich.repo
import hglib

from .gitrewrite import (
    commit_metadata_rewriter,
)
from .gitrewrite.linearize import (
    linearize_git_repo,
)


logger = logging.getLogger(__name__)


def linearize_git_repo_to_hg(git_source_url, ref, git_repo_path, hg_repo_path,
                             git_push_url=None,
                             hg_push_url=None,
                             move_to_subdir=None,
                             find_copies_harder=False,
                             skip_submodules=False,
                             similarity=50,
                             shamap_s3_upload_url=None,
                             git_commit_rewriter_args=None,
                             exclude_dirs=None):
    """Linearize a Git repo to an hg repo by squashing merges.

    Many Git repositories (especially those on GitHub) have an excessive
    number of merge commits and don't practice "every commit is
    good/bisectable." When converting these repositories to Mercurial, it is
    often desirable to ignore the non-first-parent ancestry so the result has
    more readable history.

    This function will perform such a conversion.

    The source Git repository to convert is specified by ``git_source_url``
    and ``ref``, where ``git_source_url`` is a URL understood by ``git
    clone`` and ``ref`` is a Git ref, like ``master``. Only converting
    a single ref is allowed.

    The source Git repository is locally cloned to the path ``git_repo_path``.
    This directory will be created if necessary.

    If ``git_push_url`` is specified, the local clone (including converted
    commits) will be pushed to that URL.

    If ``hg_push_url`` is specified, the converted Mercurial repo will be
    pushed to that URL.

    ``git_commit_rewriter_args`` is a dict of arguments to pass to
    ``gitrewrite.commit_metadata_rewriter()`` to construct a function for
    rewriting Git commits.

    The conversion works in phases:

    1) Git commits are rewritten into a new ref.
    2) ``hg convert`` converts the rewritten Git commits to Mercurial.

    See the docs in ``/docs/vcssync.rst`` for reasons why.

    Returns a dict describing the conversion result. The dict has the following
    keys:

    git_result
       This is a dict from ``linearize_git_repo()`` describing its results.
    rev_map_path
       Filesystem path to file mapping Git commit to Mercurial commit.
    hg_before_tip_rev
       Numeric revision of ``tip`` Mercurial changeset before conversion. ``-1``
       if the repo was empty.
    hg_before_tip_node
       SHA-1 of ``tip`` Mercurial changeset before conversion. 40 0's if the
       repo was empty.
    hg_after_tip_rev
       Numeric revision of ``tip`` Mercurial changeset before conversion.
    hg_after_tip_node
       SHA-1 of ``tip`` Mercurial changeset after conversion.
    """
    # Many processes execute with cwd=/ so normalize to absolute paths.
    git_repo_path = os.path.abspath(git_repo_path)
    hg_repo_path = os.path.abspath(hg_repo_path)

    # Create Git repo, if necessary.
    if not os.path.exists(git_repo_path):
        subprocess.check_call([b'git', b'init', b'--bare', git_repo_path])
        # We don't need to set up a remote because we use an explicit refspec
        # during fetch.

    git_repo = dulwich.repo.Repo(git_repo_path)

    subprocess.check_call([b'git', b'fetch', b'--no-tags', git_source_url,
                           b'heads/%s:heads/%s' % (ref, ref)],
                          cwd=git_repo_path)

    if git_push_url:
        subprocess.check_call([b'git', b'push', b'--mirror', git_push_url],
                              cwd=git_repo_path)

    rewriter = commit_metadata_rewriter(git_repo,
                                        source_repo=git_source_url,
                                        **git_commit_rewriter_args)

    git_state = linearize_git_repo(
        git_repo,
        b'heads/%s' % ref,
        commit_rewriter=rewriter,
        exclude_dirs=exclude_dirs)

    if git_push_url:
        subprocess.check_call([b'git', b'push', b'--mirror', git_push_url],
                              cwd=git_repo_path)

    rev_map = os.path.join(hg_repo_path, b'.hg', b'shamap')

    def maybe_push_hg():
        if not hg_push_url:
            return

        with hglib.open(hg_repo_path) as hrepo:
            logger.warn('checking for outgoing changesets to %s' % hg_push_url)
            outgoing = hrepo.outgoing(path=hg_push_url)
            if not outgoing:
                logger.warn('all changesets already in remote; no push '
                            'necessary')
                return

            # We may want to add force=True and newbranch=True here. But
            # until they are needed, go with the safe defaults.
            out = hrepo.rawcommand([b'push', hg_push_url])
            logger.warn(out)

    result = {
        'git_result': git_state,
        'rev_map_path': rev_map,
    }

    # If nothing was converted, no-op if the head is already converted
    # according to the `hg convert` revision map.
    if not git_state['commit_map']:
        try:
            with open(rev_map, 'rb') as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    shas = line.split()
                    if shas[0] == git_state['dest_commit']:
                        logger.warn('all Git commits have already been '
                                    'converted; not doing anything')
                        maybe_push_hg()
                        return result
        except IOError:
            # Fall through to doing the conversion. If it's a file permissions
            # error, `hg convert` will abort.
            pass

    logger.warn('converting %d Git commits' % len(git_state['commit_map']))

    hg_config = [
        b'extensions.convert=',
        # Make the rename detection limit essentially infinite.
        b'convert.git.renamelimit=1000000000',
        # The ``convert_revision`` that would be stored reflects the rewritten
        # Git commit. This is valuable as a persistent SHA map, but that's it.
        # We (hopefully) insert the original Git commit via
        # ``source_revision_key``, so this is of marginal value.
        b'convert.git.saverev=false',
        b'convert.git.similarity=%d' % similarity,
    ]

    if find_copies_harder:
        hg_config.append(b'convert.git.findcopiesharder=true')
    if skip_submodules:
        hg_config.append(b'convert.git.skipsubmodules=true')

    if not os.path.exists(hg_repo_path):
        hglib.init(hg_repo_path)

    with hglib.open(hg_repo_path) as hrepo:
        tip = hrepo[b'tip']
        before_hg_tip_rev = tip.rev()
        before_hg_tip_node = tip.node()

    shamap_path = os.path.join(hg_repo_path, b'.hg', b'shamap')
    def get_shamap_hash():
        if not os.path.exists(shamap_path):
            return None

        with open(shamap_path, 'rb') as fh:
            return hashlib.sha256(fh.read()).digest()

    old_shamap_hash = get_shamap_hash()

    args = [hglib.HGPATH]
    for c in hg_config:
        args.extend([b'--config', c])

    args.extend([b'convert'])
    args.extend([b'--rev', b'refs/convert/dest/heads/%s' % ref])

    # `hg convert` needs a filemap to prune empty changesets. So use an
    # empty file even if we don't have any filemap rules.
    with tempfile.NamedTemporaryFile('wb') as tf:
        if move_to_subdir:
            tf.write(b'rename . %s\n' % move_to_subdir)

        tf.flush()

        args.extend([b'--filemap', tf.name])

        args.extend([git_repo_path, hg_repo_path, rev_map])

        # hglib doesn't appear to stream output very well. So just invoke
        # `hg` directly.
        env = dict(os.environ)
        env[b'HGPLAIN'] = b'1'
        env[b'HGENCODING'] = b'utf-8'

        subprocess.check_call(args, cwd='/', env=env)

    with hglib.open(hg_repo_path) as hrepo:
        tip = hrepo[b'tip']
        after_hg_tip_rev = tip.rev()
        after_hg_tip_node = tip.node()

    if before_hg_tip_rev == -1:
        convert_count = after_hg_tip_rev + 1
    else:
        convert_count = after_hg_tip_rev - before_hg_tip_rev

    result['hg_before_tip_rev'] = before_hg_tip_rev
    result['hg_after_tip_rev'] = after_hg_tip_rev
    result['hg_before_tip_node'] = before_hg_tip_node
    result['hg_after_tip_node'] = after_hg_tip_node
    result['hg_convert_count'] = convert_count

    logger.warn('%d Git commits converted to Mercurial; '
                'previous tip: %d:%s; current tip: %d:%s' % (
        convert_count, before_hg_tip_rev, before_hg_tip_node,
        after_hg_tip_rev, after_hg_tip_node))

    maybe_push_hg()

    # TODO so hacky. Relies on credentials in the environment.
    if shamap_s3_upload_url and old_shamap_hash != get_shamap_hash():
        subprocess.check_call([
            b'aws', b's3', b'cp', shamap_path, shamap_s3_upload_url
        ])

    return result
