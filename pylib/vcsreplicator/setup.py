from setuptools import setup, find_packages

setup(
    name='vcsreplicator',
    version='0.1',
    description='Replicate changes between version control systems',
    url='https://mozilla-version-control-tools.readthedocs.org/',
    author='Mozilla',
    author_email='dev-version-control@lists.mozilla.org',
    license='MPL 2.0',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 2.7',
    ],
    packages=find_packages(),
    install_requires=['kafka-python', 'Mercurial'],
)
