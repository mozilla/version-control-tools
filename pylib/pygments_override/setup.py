from reviewboard.extensions.packaging import setup


PACKAGE = 'pygments_override'
VERSION = '0.1.0'

setup(
    name=PACKAGE,
    version=VERSION,
    description='Customize Pygments for specific file extensions',
    author='Salvador de la Puente',
    author_email='salva@mozilla.com',
    license='MPL 2.0',
    packages=['pygments_override'],
    entry_points={
        'reviewboard.extensions':
        '%s = pygments_override.extension:PygmentsOverride' % PACKAGE,
    }
)
