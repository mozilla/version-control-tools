from setuptools import setup, find_packages

setup(
    name='mozxchannel',
    version='0.1',
    description='Unify localized strings across repositories and channels',
    url='https://mozilla-version-control-tools.readthedocs.io/',
    author='Mozilla',
    author_email='dev-version-control@lists.mozilla.org',
    license='GPL 2.0',
    classifiers=[
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 2.7',
    ],
    packages=find_packages(),
    entry_points={
        'console_scripts': [
        ],
    },
    install_requires=[
        'Mercurial>=4.2.1',
    ],
)
