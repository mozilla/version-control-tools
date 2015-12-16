from setuptools import setup, find_packages

setup(
    name='pushlog_client',
    version='0.2.0',
    packages=find_packages(),

    install_requires=[
        'requests>=2.8.1'
    ],

    # Meta-data for upload to PyPI
    author='Armen Zambrano G.',
    author_email='armenzg@mozilla.com',
    description="Script designed to query information about who pushes what where and when.",
    license='MPL2',
    url='https://hg.mozilla.org/hgcustom/version-control-tools/file/tip/pylib/mozhginfo',
)
