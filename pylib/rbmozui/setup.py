#!/usr/bin/env python
from reviewboard.extensions.packaging import setup
from setuptools import find_packages

from rbmozui import get_package_version


PACKAGE_NAME = "rbmozui"


setup(
    name=PACKAGE_NAME,
    version=get_package_version(),
    license="MIT",
    description="UI tweaks to Review Board for Mozilla",
    packages=find_packages(),
    install_requires=[
        'ReviewBoard>=2.0.2',
    ],
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
    ],
    entry_points={
        'reviewboard.extensions':
            '%s = rbmozui.extension:RBMozUI' % PACKAGE_NAME,
    },
    package_data={
        'rbmozui': [
            'templates/rbmozui/*.txt',
            'templates/rbmozui/*.html',
            'static/css/*.css',
            'static/css/*.less'
        ],
    }
)
