from setuptools import setup, find_packages

required = [
    'requests>=2.8.1',
    'redo>=1.5'
]

setup(
    name='pushlog_client',
    version='0.6.0',
    packages=find_packages(),

    install_requires=required,
    tests_require=required + ['mock', 'pytest'],

    # Meta-data for upload to PyPI
    author='Armen Zambrano G.',
    author_email='armenzg@mozilla.com',
    description="Script designed to query information about who pushes what where and when.",
    license='MPL2',
    url='https://hg.mozilla.org/hgcustom/version-control-tools/file/tip/pylib/mozhginfo',
)
