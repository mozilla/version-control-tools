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
import transplant
sys.path = SYS_PATH


class TestAutoland(unittest.TestCase):

    def test_transplant_to_mozreview(self):
        local_repo_path = tempfile.mkdtemp()
        mozreview_repo_path = tempfile.mkdtemp()

        try:
            cmds = [['hg', 'init'],
                    ['hg', 'bookmark', 'central']]

            for cmd in cmds:
                subprocess.check_call(cmd, cwd=local_repo_path)

            with open(os.path.join(local_repo_path, '.hg', 'hgrc'), 'w') as f:
                f.write('[paths]\nmozreview = ')
                f.write(mozreview_repo_path)
                f.write('\n')

            def get_repo_path(tree):
                return local_repo_path
            transplant.get_repo_path = get_repo_path

            transplant.github.connect = mock.Mock()
            def retrieve_commits(gh, user, repo, pullrequest, path):
                shutil.copy(os.path.join(HERE, 'test-data', 'patch.txt'),
                            local_repo_path)
                return ['patch.txt']
            transplant.github.retrieve_commits = retrieve_commits

            landed, result = transplant.transplant_to_mozreview('mozilla',
                                                                'cthulhu',
                                                                'repo', 0)

            # We expect this to not be landed as we're not pushing to a repo
            # with the mozreview extension, but we should not see an error in
            # the result.
            self.assertEqual(landed, False)
            self.assertEqual(result, '')

            output = 'review url: http://localhost:55557/r/1 (pending)'
            m = re.search(transplant.REVIEW_REXP, output)
            self.assertIsNotNone(m)
            self.assertEqual(m.groups()[0], '1')

        finally:
            shutil.rmtree(local_repo_path)
            shutil.rmtree(mozreview_repo_path)

    def test_transplant_to_try(self):
        mozreview_repo_path = tempfile.mkdtemp()
        try_repo_path = tempfile.mkdtemp()
        local_repo_path = tempfile.mkdtemp()

        try:
            # Configure 'mozreview' repo
            shutil.copy(os.path.join(HERE, 'test-data', 'patch.txt'),
                        mozreview_repo_path)
            cmds = [['hg', 'init'],
                    ['hg', 'import', 'patch.txt']]
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
                    ['hg', 'bookmark', 'central']]
            for cmd in cmds:
                subprocess.check_call(cmd, cwd=local_repo_path)

            with open(os.path.join(local_repo_path, '.hg', 'hgrc'), 'w') as f:
                f.write('[paths]\ntry = ')
                f.write(try_repo_path)
                f.write('\nmozreview = ')
                f.write(mozreview_repo_path)
                f.write('\n')

            def get_repo_path(tree):
                return local_repo_path
            transplant.get_repo_path = get_repo_path

            landed, result = transplant.transplant_to_try('mozilla', '0',
                                                          'try')

            # We expect this to not be landed as we're not pushing to try, but
            # we should not see an error in the result.
            self.assertEqual(landed, False)
            self.assertEqual(result, '')

            output = 'remote:   https://hg.mozilla.org/try/rev/f4a5dc70834d'
            m = re.search(transplant.HGMO_REXP, output)
            self.assertIsNotNone(m)
            self.assertEqual(m.groups()[0], 'f4a5dc70834d')

        finally:
            shutil.rmtree(local_repo_path)
            shutil.rmtree(mozreview_repo_path)
            shutil.rmtree(try_repo_path)


if __name__ == '__main__':
    unittest.main()
