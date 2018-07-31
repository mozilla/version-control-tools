# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import, unicode_literals

import io
import json
import logging
import os
from pipes import quote
import shutil
import subprocess
import tempfile
import zipfile

import boto3

from .vctutil import (
    get_and_write_vct_node,
)

HERE = os.path.abspath(os.path.dirname(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
ANSIBLE = os.path.join(ROOT, 'ansible')

logger = logging.getLogger(__name__)


def run_playbook(name, extra_vars=None, verbosity=0):
    get_and_write_vct_node()

    extra_vars = extra_vars or {}

    args = [
        'ansible-playbook',
        '-i', os.path.join(ANSIBLE, 'hosts'),
        '-f', '20',
        '%s.yml' % name,
        '--extra-vars', json.dumps(extra_vars),
    ]
    if verbosity:
        args.append('-%s' % ('v' * verbosity))

    logger.info('$ %s' % ' '.join([quote(a) for a in args]))
    return subprocess.call(args, cwd=ANSIBLE)


def deploy_mozreview_prod(repo=None, rev=None, rb_repo=None, rb_rev=None,
                          verbosity=0):
    extra = {'vct': ROOT}
    if repo:
        extra['repo'] = repo
    if rev:
        extra['rev'] = rev
    if rb_repo:
        extra['rb_repo'] = rb_repo
    if rb_rev:
        extra['rb_rev'] = rb_rev

    return run_playbook('deploy-mozreview-prod', extra_vars=extra,
                        verbosity=verbosity)


def mozreview_create_repo(verbosity=0):
    extra = {'vct': ROOT}
    return run_playbook('mozreview-create-repo', extra_vars=extra,
                        verbosity=verbosity)


def deploy_hgmo(skip_hgssh=False, skip_hgweb=False, verbosity=0):
    """Deploy to hg.mozilla.org."""
    extra = {
        'skip_hgssh': skip_hgssh,
        'skip_hgweb': skip_hgweb,
        'vct': ROOT,
    }

    return run_playbook('deploy-hgmo', extra_vars=extra,
                        verbosity=verbosity)


def deploy_vcs_sync(verbosity=0):
    extra = {'vct': ROOT}
    return run_playbook('vcssync-deploy', extra_vars=extra,
                        verbosity=verbosity)


def hgmo_strip(repo, rev, verbosity=0):
    extra = {
        'repo': repo,
        'rev': rev,
    }

    return run_playbook('hgmo-strip-repo', extra_vars=extra,
                        verbosity=verbosity)


def hgmo_reclone_repos(repos, verbosity=0):
    extra = {'repos': repos}

    return run_playbook('hgmo-reclone-repos', extra_vars=extra,
                        verbosity=verbosity)

def github_lambda_deploy_package():
    """Obtain a .zip file for a deployment package for GitHub Lambda foo."""
    d = tempfile.mkdtemp()

    PIP = os.path.join(ROOT, 'venv', 'bin', 'pip')

    try:
        # Install Python packages.
        subprocess.check_call([
            PIP, 'install',
            '-t', d,
            '-r', os.path.join(ROOT, 'github-webhooks', 'lambda-requirements.txt'),
            '--require-hashes',
        ])

        # Copy relevant files from the source directory.
        for p in os.listdir(os.path.join(ROOT, 'github-webhooks')):
            if not p.endswith('.py'):
                continue

            shutil.copyfile(os.path.join(ROOT, 'github-webhooks', p),
                            os.path.join(d, p))

        # Now make a zip file.
        zf = io.BytesIO()
        with zipfile.ZipFile(zf, 'w') as z:
            for root, dirs, files in os.walk(d):
                for f in sorted(files):
                    full = os.path.join(root, f)
                    rel = os.path.relpath(full, d)

                    z.write(full, rel)

        return zf.getvalue()
    finally:
        shutil.rmtree(d)


def github_webhook_lambda():
    """Deploys code for GitHub WebHook processing in AWS Lambda."""
    zip_content = github_lambda_deploy_package()

    S3_BUCKET = 'moz-github-webhooks'
    S3_KEY = 'github_lambda.zip'

    # The code package is shared. So upload to S3 and reference it there.
    s3 = boto3.client('s3')
    s3.put_object(
        Bucket=S3_BUCKET,
        Key=S3_KEY,
        Body=zip_content,
        ContentType='application/zip',
    )

    client = boto3.client('lambda', region_name='us-west-2')

    for fn in ('github-webhooks-receive', 'github-webhooks-pulse'):
        res = client.update_function_code(
            FunctionName=fn,
            S3Bucket=S3_BUCKET,
            S3Key=S3_KEY,
            Publish=True,
        )

        # Lambda versions code/functions by default. So delete old versions
        # as part of upload so old versions don't pile up.
        for v in client.list_versions_by_function(FunctionName=fn)['Versions']:
            if v['Version'] in (res['Version'], '$LATEST'):
                continue

            client.delete_function(
                FunctionName=v['FunctionArn'],
                Qualifier=v['Version'])
