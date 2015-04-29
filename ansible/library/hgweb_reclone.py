#!/usr/bin/env python
# This software may be used and distributed according to the terms of the
# GNU General Public License version 3 or any later version.

# While this module could be represented by Ansible tasks, we need the ability
# to paramatize roles or includes with with_items, which isn't supported by
# Ansible 1.x. This module is a workaround.

import os
import shutil


DOCUMENTATION = '''
---
module: hgweb_reclone
short_description: Re-clone repositories on an hgweb mirror
options:
  repo:
    description:
      - Relative path of repository to re-clone
    required: true
'''


def main():
    module = AnsibleModule(argument_spec={'repo': {'required': True}})

    repo = module.params['repo']

    repo_path = os.path.join('/repo/hg/mozilla', repo)

    if os.path.exists(repo_path):
        shutil.rmtree(repo_path)

    mp = ['/usr/bin/sudo', '-u', 'hg', '/usr/local/bin/mirror-pull']

    # Create the empty repo.
    #
    # `mirror-pull <repo>` could be used to create the repo from scratch.
    # However, mirror-pull takes out a global lock during `hg clone`. This
    # effectively prevents multiple repositories from being created
    # simultaneously. This lock adds little value, as Mercurial itself performs
    # repo-level locking where appropriate. But the lock exists, so work around
    # it.
    module.run_command(['/usr/bin/sudo', '-u', 'hg', 'hg', 'init', repo_path],
                       check_rc=True)

    # Pull repo.
    module.run_command(mp + [repo], check_rc=True)

    # Restore hgrc
    module.run_command(mp + ['--hgrc', repo], check_rc=True)

    # Pull again in case upstream changed
    module.run_command(mp + [repo], check_rc=True)

    module.exit_json(changed=True, msg='Re-cloned %s' % repo)


from ansible.module_utils.basic import *
main()
