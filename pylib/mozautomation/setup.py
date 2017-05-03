from setuptools import setup

# ansible/roles/vcs-sync/defaults/main.yml must be updated if this package's
# version number is changed.

setup(
    name='mozautomation',
    version='0.2',
    description="Support packages for interacting with parts of Mozilla's "
                "automation infrastructure",
    author='Mozilla Developer Services',
    packages=['mozautomation'],
)
