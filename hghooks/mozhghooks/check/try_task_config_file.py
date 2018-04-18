# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

from __future__ import absolute_import


from ..checks import (
    PreTxnChangegroupCheck,
    print_banner,
)


TRY_CONFIG_FOUND = """
You are trying to commit the temporary 'try_task_config.json' file
on a non-try branch. Either make sure you are pushing to try or
remove the file and push again.
"""


class TryConfigCheck(PreTxnChangegroupCheck):
    """Prevents the try_task_config.json file from being committed.

    Try infrastructure may produce a special ``try_task_config.json`` file
    in the repository. We don't want to allow this file to exist in the main
    Firefox repositories.
    """
    @property
    def name(self):
        return 'try_task_config'

    def relevant(self):
        return self.repo_metadata['firefox_releasing']

    def pre(self, node):
        pass

    def check(self, ctx):
        if 'try_task_config.json' not in ctx.files():
            return True

        print_banner(self.ui, 'error', TRY_CONFIG_FOUND)
        return False

    def post_check(self):
        return True
