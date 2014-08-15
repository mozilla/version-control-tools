# This is a distutils setup script for the mozhghooks module.
# Install the module by running `python setup.py install`

from setuptools import setup

setup(name="Mozilla Hg Hooks",
      version='0.1',
      description="Mozilla-specific hooks for Mercurial VCS",
      author="Ted Mielczarek",
      author_email="ted.mielczarek@gmail.com",
      packages=["mozhghooks"]
)
