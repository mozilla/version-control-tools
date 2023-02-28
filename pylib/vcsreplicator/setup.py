import sys
from setuptools import setup, find_packages

install_requires = [
    "cbor2",
    "kafka-python",
    "Mercurial",
    "python-hglib",
]

setup(
    name="vcsreplicator",
    version="0.1",
    description="Replicate changes between version control systems",
    url="https://mozilla-version-control-tools.readthedocs.io/",
    author="Mozilla",
    author_email="dev-version-control@lists.mozilla.org",
    license="MPL 2.0",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 2.7",
    ],
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "check_vcsreplicator_lag=vcsreplicator.nagios:check_consumer_lag",
            "check_vcsreplicator_aggregator_lag=vcsreplicator.nagios:check_aggregator_lag",
            "vcsreplicator-aggregator=vcsreplicator.aggregator:cli",
            "vcsreplicator-consumer=vcsreplicator.consumer:consumer_cli",
            "vcsreplicator-headsconsumer=vcsreplicator.consumer:heads_consumer_cli",
            "vcsreplicator-print-offsets=vcsreplicator.consumer:print_offsets",
            "vcsreplicator-pulse-notifier=vcsreplicator.pulsenotifier:cli",
            "vcsreplicator-sns-notifier=vcsreplicator.snsnotifier:cli",
            "vcsreplicator-bootstrap-hgssh=vcsreplicator.bootstrap:hgssh",
            "vcsreplicator-bootstrap-hgweb=vcsreplicator.bootstrap:hgweb",
        ],
    },
    install_requires=install_requires,
)
