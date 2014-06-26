from setuptools import setup

PACKAGE = 'rbbz'
VERSION = '0.1.11'

setup(name=PACKAGE,
      version=VERSION,
      description='Review Board extension for Bugzilla support',
      url='https://github.com/mozilla/rbbz',
      author='Mark Cote',
      author_email='mcote@mozilla.com',
      license='MPL 2.0',
      packages=['rbbz'],
      entry_points={
          'reviewboard.extensions':
              '%s = rbbz.extension:BugzillaExtension' % PACKAGE,
          'reviewboard.auth_backends': [
              'bugzilla = rbbz.auth:BugzillaBackend',
          ],
      }
)
