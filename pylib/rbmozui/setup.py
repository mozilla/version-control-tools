from reviewboard.extensions.packaging import setup


PACKAGE = "rbmozui"
VERSION = "0.1"

setup(
    name=PACKAGE,
    version=VERSION,
    description="UI tweaks to Review Board for Mozilla",
    author="Mike Conley",
    packages=["rbmozui"],
    entry_points={
        'reviewboard.extensions':
            '%s = rbmozui.extension:RBMozUI' % PACKAGE,
    },
    package_data={
        'rbmozui': [
            'templates/rbmozui/*.txt',
            'templates/rbmozui/*.html',
        ],
    }
)
