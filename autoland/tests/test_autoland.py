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

@unittest.skip('this test needs to be rewritten as a .t test')
class TestAutoland(unittest.TestCase):

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
        inbound_repo_path = tempfile.mkdtemp()
        local_repo_path = tempfile.mkdtemp()
        mozreview_repo_path = tempfile.mkdtemp()
        upstream_repo_path = tempfile.mkdtemp()

        try:
            # Configure 'upstream' repo
            cmds = [['hg', 'init']]
            for cmd in cmds:
                subprocess.check_call(cmd, cwd=upstream_repo_path)

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

            # Configure 'inbound' repo
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
            shutil.rmtree(upstream_repo_path)

    def test_transplant_using_at_bookmark(self):
        inbound_repo_path = tempfile.mkdtemp()
        local_repo_path = tempfile.mkdtemp()
        mozreview_repo_path = tempfile.mkdtemp()
        upstream_repo_path = tempfile.mkdtemp()

        try:
            # Configure 'upstream' repo
            cmds = [['hg', 'init']]
            for cmd in cmds:
                subprocess.check_call(cmd, cwd=upstream_repo_path)

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

            # Configure 'inbound' repo
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
            shutil.rmtree(upstream_repo_path)

    def test_rewrite_descriptions(self):
        inbound_repo_path = tempfile.mkdtemp()
        local_repo_path = tempfile.mkdtemp()
        mozreview_repo_path = tempfile.mkdtemp()
        upstream_repo_path = tempfile.mkdtemp()

        try:
            # Configure 'upstream' repo
            cmds = [['hg', 'init']]
            for cmd in cmds:
                subprocess.check_call(cmd, cwd=upstream_repo_path)

            # Configure 'mozreview' repo
            for f in ['initial.patch', 'added-blah.patch']:
                shutil.copy(os.path.join(HERE, 'test-data', f),
                            mozreview_repo_path)
            cmds = [['hg', 'init'],
                    ['hg', 'import', 'initial.patch'],
                    ['hg', 'import', 'added-blah.patch'],
                    ['hg', 'log', '-r', '.', '--template', '{node|short}']]
            for cmd in cmds:
                # Use check_output to suppress the output from hg import
                rev = subprocess.check_output(cmd, stderr=subprocess.STDOUT,
                                              cwd=mozreview_repo_path)
            with open(os.path.join(mozreview_repo_path, '.hg', 'hgrc'), 'w') as f:
                f.write('[phases]\npublish = False\n')

            # Configure 'inbound' repo
            shutil.copy(os.path.join(HERE, 'test-data', 'initial.patch'),
                        inbound_repo_path)
            cmds = [['hg', 'init'],
                    ['hg', 'import', 'initial.patch']]
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
                f.write(upstream_repo_path)
                f.write('\n')

                ext = os.path.join(os.path.split(HERE)[0], 'hgext', 'rewritecommitdescriptions.py')
                f.write('[extensions]\n')
                f.write('rewritecommitdescriptions = %s\n\n' % ext)

            def get_repo_path(tree):
                return local_repo_path
            transplant.get_repo_path = get_repo_path

            commit_descriptions = {'1cf8d88f5d98': 'please rewrite me!'}

            landed, result = transplant.transplant('mozreview', 'inbound',
                                                   '1cf8d88f5d98',
                                                   commit_descriptions=commit_descriptions)
            self.assertEqual(landed, True)
            self.assertEqual(len(result), 12)
            self.assertIsNotNone(re.match('([a-f0-9]+)', result))

            # Check that we rewrote as expected
            cmds = [['hg', 'log', '-r', 'tip']]
            for cmd in cmds:
                result = subprocess.check_output(cmd, cwd=inbound_repo_path)
            self.assertTrue('please rewrite me!' in result)

        finally:
            shutil.rmtree(inbound_repo_path)
            shutil.rmtree(local_repo_path)
            shutil.rmtree(mozreview_repo_path)
            shutil.rmtree(upstream_repo_path)


if __name__ == '__main__':
    unittest.main()
