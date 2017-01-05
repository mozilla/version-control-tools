from setuptools import setup, find_packages

setup(
    name='mozvcssync',
    version='0.1',
    description='Synchronize changes across VCS repositories',
    url='https://mozilla-version-control-tools.readthedocs.io/',
    author='Mozilla',
    author_email='dev-version-control@lists.mozilla.org',
    license='MPL 2.0',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 2.7',
    ],
    packages=find_packages(),
    install_requires=['Mercurial>=4.0'],
)
