from setuptools import setup, find_packages

setup(
    name='mozreviewbots',
    version='0.1',
    description='MozReview static analysis bots',
    url='https://mozilla-version-control-tools.readthedocs.org/',
    author='Mozilla',
    author_email='dev-version-control@lists.mozilla.org',
    license='MPL 2.0',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'Programming Language :: Python :: 2.7',
    ],
    packages=find_packages(),
    install_requires=['RBTools', 'kombu'],
)
