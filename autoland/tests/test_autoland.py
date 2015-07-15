import copy
import mock
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.split(os.path.realpath(__file__))[0]

SYS_PATH = copy.copy(sys.path)
sys.path.append(os.path.join(os.path.split(HERE)[0], 'autoland'))
import autoland
import github
import transplant
sys.path = SYS_PATH


class TestAutoland(unittest.TestCase):

    def test_transplant_to_mozreview(self):
        local_repo_path = tempfile.mkdtemp()
        mozreview_repo_path = tempfile.mkdtemp()

        shutil.copy(os.path.join(HERE, 'test-data', 'initial.patch'),
                    local_repo_path)
        try:
            cmds = [['hg', 'init'],
                    ['hg', 'import', 'initial.patch'],
                    ['hg', 'phase', '--public', '-r', '.'],
                    ['hg', 'bookmark', 'upstream']]

            for cmd in cmds:
                # Use check_output to suppress the output from hg import
                subprocess.check_output(cmd, stderr=subprocess.STDOUT,
                                        cwd=local_repo_path)
            with open(os.path.join(local_repo_path, '.hg', 'hgrc'), 'w') as f:
                f.write('[extensions]\npurge =\n')
                f.write('[paths]\nmozreview-push = ')
                f.write(mozreview_repo_path)
                f.write('\n')
                f.write('upstream = .\n')

            cmds = [['hg', 'init']]
            for cmd in cmds:
                # Use check_output to suppress the output from hg import
                subprocess.check_output(cmd, stderr=subprocess.STDOUT,
                                        cwd=mozreview_repo_path)

            with open(os.path.join(mozreview_repo_path, '.hg', 'hgrc'), 'w') as f:
                f.write('[phases]\npublish = False\n')

            def get_repo_path(tree):
                return local_repo_path
            transplant.get_repo_path = get_repo_path

            class RetrieveCommits():
                def __init__(self):
                    self.files = [['rename-file.patch'],
                                  ['added-blah.patch']]
                    self.current = 0

                def __call__(self, gh, user, repo, pullrequest, path):
                    if self.current > len(self.files):
                        return []
                    else:
                        files = self.files[self.current]
                        self.current += 1
                        for f in files:
                            shutil.copy(os.path.join(HERE, 'test-data', f),
                                        local_repo_path)
                    return files

            gh = mock.Mock()
            github.retrieve_commits = RetrieveCommits()

            # land a patch with a rename
            landed, result = transplant.transplant_to_mozreview(gh, 'mozilla',
                                                                'cthulhu',
                                                                'repo', 0,
                                                                0, 'cookie', 0)

            # We expect this to not be landed as we're not pushing to a repo
            # with the mozreview extension, but we should not see an error in
            # the result.
            self.assertEqual(landed, False)
            self.assertEqual(result, '')

            # ensure patches are applied independently - this should fail if
            # we still see the rename above.
            cmds = [['hg', 'strip', '--no-backup', '-r', 'draft()']]
            for cmd in cmds:
                subprocess.check_call(cmd, stderr=subprocess.STDOUT,
                                      cwd=mozreview_repo_path)

            landed, result = transplant.transplant_to_mozreview(gh, 'mozilla',
                                                                'cthulhu',
                                                                'repo', 0, 0,
                                                                'cookie', 0)
            self.assertEqual(landed, False)
            self.assertEqual(result, '')
            self.assertTrue(os.path.isfile(os.path.join(local_repo_path,
                            'hello')))

            # simple test of rexp to extract review id
            output = 'review url: http://localhost:55557/r/1 (pending)'
            m = re.search(transplant.REVIEW_REXP, output)
            self.assertIsNotNone(m)
            self.assertEqual(m.groups()[0], 'http://localhost:55557/r/1')

        finally:
            shutil.rmtree(local_repo_path)
            shutil.rmtree(mozreview_repo_path)

    def test_transplant_to_try(self):
        mozreview_repo_path = tempfile.mkdtemp()
        try_repo_path = tempfile.mkdtemp()
        local_repo_path = tempfile.mkdtemp()

        try:
            # Configure 'mozreview' repo
            shutil.copy(os.path.join(HERE, 'test-data', 'initial.patch'),
                        mozreview_repo_path)
            cmds = [['hg', 'init'],
                    ['hg', 'import', 'initial.patch']]
            for cmd in cmds:
                # Use check_output to suppress the output from hg import
                subprocess.check_output(cmd, stderr=subprocess.STDOUT,
                                        cwd=mozreview_repo_path)
            with open(os.path.join(mozreview_repo_path, '.hg', 'hgrc'), 'w') as f:
                f.write('[phases]\npublish = False\n')

            # Configure 'try' repo
            cmds = [['hg', 'init']]
            for cmd in cmds:
                subprocess.check_call(cmd, cwd=try_repo_path)
            with open(os.path.join(try_repo_path, '.hg', 'hgrc'), 'w') as f:
                f.write('[phases]\npublish = False\n')

            # Configure 'local' repo
            cmds = [['hg', 'init'],
                    ['hg', 'bookmark', 'upstream']]
            for cmd in cmds:
                subprocess.check_call(cmd, cwd=local_repo_path)

            with open(os.path.join(local_repo_path, '.hg', 'hgrc'), 'w') as f:
                f.write('[paths]\ntry = ')
                f.write(try_repo_path)
                f.write('\nmozreview = ')
                f.write(mozreview_repo_path)
                f.write('\nupstream= ')
                f.write(mozreview_repo_path)
                f.write('\n')

            def get_repo_path(tree):
                return local_repo_path
            transplant.get_repo_path = get_repo_path

            landed, result = transplant.transplant('mozreview', 'try', '0',
                                                   'try')
            self.assertEqual(landed, True)
            self.assertEqual(len(result), 12)
            self.assertIsNotNone(re.match('([a-f0-9]+)', result))

        finally:
            shutil.rmtree(local_repo_path)
            shutil.rmtree(mozreview_repo_path)
            shutil.rmtree(try_repo_path)

    def test_transplant_to_inbound(self):
        mozreview_repo_path = tempfile.mkdtemp()
        inbound_repo_path = tempfile.mkdtemp()
        local_repo_path = tempfile.mkdtemp()

        try:
            # Configure 'mozreview' repo
            shutil.copy(os.path.join(HERE, 'test-data', 'initial.patch'),
                        mozreview_repo_path)
            cmds = [['hg', 'init'],
                    ['hg', 'import', 'initial.patch']]
            for cmd in cmds:
                # Use check_output to suppress the output from hg import
                subprocess.check_output(cmd, stderr=subprocess.STDOUT,
                                        cwd=mozreview_repo_path)
            with open(os.path.join(mozreview_repo_path, '.hg', 'hgrc'), 'w') as f:
                f.write('[phases]\npublish = False\n')

            # Configure 'try' repo
            cmds = [['hg', 'init']]
            for cmd in cmds:
                subprocess.check_call(cmd, cwd=inbound_repo_path)

            # Configure 'local' repo
            cmds = [['hg', 'init'],
                    ['hg', 'bookmark', 'upstream']]
            for cmd in cmds:
                subprocess.check_call(cmd, cwd=local_repo_path)

            with open(os.path.join(local_repo_path, '.hg', 'hgrc'), 'w') as f:
                f.write('[paths]\ninbound = ')
                f.write(inbound_repo_path)
                f.write('\nmozreview = ')
                f.write(mozreview_repo_path)
                f.write('\nupstream= ')
                f.write(mozreview_repo_path)
                f.write('\n')

            def get_repo_path(tree):
                return local_repo_path
            transplant.get_repo_path = get_repo_path

            landed, result = transplant.transplant('mozreview', 'inbound', '0')
            self.assertEqual(landed, True)
            self.assertEqual(len(result), 12)
            self.assertIsNotNone(re.match('([a-f0-9]+)', result))

        finally:
            shutil.rmtree(local_repo_path)
            shutil.rmtree(mozreview_repo_path)
            shutil.rmtree(inbound_repo_path)

    def test_transplant_using_at_bookmark(self):
        mozreview_repo_path = tempfile.mkdtemp()
        inbound_repo_path = tempfile.mkdtemp()
        local_repo_path = tempfile.mkdtemp()

        try:
            # Configure 'mozreview' repo
            shutil.copy(os.path.join(HERE, 'test-data', 'initial.patch'),
                        mozreview_repo_path)
            cmds = [['hg', 'init'],
                    ['hg', 'import', 'initial.patch']]
            for cmd in cmds:
                # Use check_output to suppress the output from hg import
                subprocess.check_output(cmd, stderr=subprocess.STDOUT,
                                        cwd=mozreview_repo_path)
            with open(os.path.join(mozreview_repo_path, '.hg', 'hgrc'), 'w') as f:
                f.write('[phases]\npublish = False\n')

            # Configure 'try' repo
            cmds = [['hg', 'init']]
            for cmd in cmds:
                subprocess.check_call(cmd, cwd=inbound_repo_path)

            # Configure 'local' repo
            cmds = [['hg', 'init'],
                    ['hg', 'bookmark', 'upstream']]
            for cmd in cmds:
                subprocess.check_call(cmd, cwd=local_repo_path)

            with open(os.path.join(local_repo_path, '.hg', 'hgrc'), 'w') as f:
                f.write('[paths]\nversion-control-tools = ')
                f.write(inbound_repo_path)
                f.write('\nmozreview = ')
                f.write(mozreview_repo_path)
                f.write('\nupstream= ')
                f.write(mozreview_repo_path)
                f.write('\n')

            def get_repo_path(tree):
                return local_repo_path
            transplant.get_repo_path = get_repo_path

            landed, result = transplant.transplant('mozreview',
                                                   'version-control-tools',
                                                   '0', '', '@')
            self.assertEqual(landed, True)
            self.assertEqual(len(result), 12)
            self.assertIsNotNone(re.match('([a-f0-9]+)', result))

        finally:
            shutil.rmtree(local_repo_path)
            shutil.rmtree(mozreview_repo_path)
            shutil.rmtree(inbound_repo_path)


if __name__ == '__main__':
    unittest.main()
