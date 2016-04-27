autoland
========

Overview
--------

Autoland is a tool that automatically lands patches from one tree to another.
It also monitors test runs and re-triggers jobs automatically to help determine
if failures are due to intermittents or not.

Currently Autoland is aimed at automatically landing patches from MozReview [1]
to Try [2] to allow for patches to be easily pushed to Try during the review
process.

A Web API is exposed to allow for try requests to be made at /autoland. This
endpoint expects a json structure to be posted to it with mime-type
"application/json". It is protected by HTTP Basic Auth.

The posted structure must be as follows:


    {
      "tree": "mozilla-central",
      "revision": "9cc25f7ac50a",
      "destination": "try",
      "trysyntax": "try: -b o -p linux -u mochitest-1 -t none",
      "pingback_url": "http://localhost/mozreview"
    }


The tree and revision specify the source of the patch to be autolanded. The
destination determines where the patch will be landed. The trysyntax, which is
optional, provides the additional trysyntax to be used if the destination tree
is Try. The endpoint provides a callback url which is hit once the patch has
been attempted to be landed.

A successful request returns a 200 and a json encoded structure containing a
request_id that can be used to determine the status of the autoland request:


    {
      "request_id": 42
    }


A simple script which posts to this endpoint using the Python requests library
can be found under testing/utils/post-job.py.

The callback json structure looks like the following:


    {
      "request_id": 42,
      "tree": "mozilla-central",
      "rev": "9cc25f7ac50a",
      "destination": "try",
      "trysyntax": "try: -b o -p linux -u mochitest-1 -t none",
      "landed": true,
      "result": "1f34accb7920",
      "error_msg": ""
    }


The request_id matches the request_id returned for the initial request. The
tree, revision, destination and try_syntax fields match what was passed in the
initial request. The landed field is true if the patch was successfully landed
and false otherwise. The result field has the SHA1 of the new revision if the
patch was successfully landed, otherwise, the error_msg field will contain
an error message.

A status API is also provided under autoland/request/<id> which allows for the
status of a request to be queried. The json structure returned looks like the
following:


    {
      "tree": "mozilla-central",
      "rev": "9cc25f7ac50a",
      "destination": "try",
      "trysyntax": "try: -b o -p linux -u mochitest-1 -t none",
      "landed": true,
      "result": "1f34accb7920"
      "error_msg": ""
    }


[1] https://mozilla-version-control-tools.readthedocs.io/en/latest/mozreview.html

[2] http://hg.mozilla.org/try


Design
------

Autoland consists of three components which run independently. A Flask based
Web API listens for incoming autoland requests. A Pulse [1] listener listens
for build started and finished messages and uses these to update test runs
which are being monitored. The main autoland service periodically queries for
pending autoland requests and monitored test runs which require servicing. A
Postgres database is used to track autoland request and test run state.

Autoland requests are serviced by using mercurial commands to move the commit
from one repository to another. If the destination repository is Try, the
resulting test run will then be monitored and any failures will be retriggered
exactly once as a means of dealing with intermittent failures.

[1] https://pulse.mozilla.org/

Installation
------------

Many of the defaults here assume that Autoland is installed under
/home/ubuntu/version-control-tools/autoland. You will need to adjust the
configuration if this is not the case.

If not already present, install mercurial from
https://www.mercurial-scm.org/downloads rather than relying upon the version
present in the ubuntu packages.

Install required ubuntu packages:

    sudo apt-get update
    sudo apt-get install python-pip python-dev postgresql libpq-dev \
                         libldap2-dev libsasl2-dev python-virtualenv

Create and activate a virtualenv:

    cd version-control-tools/autoland
    virtualenv venv
    . venv/bin/activate

Install python libs

    pip install -r requirements.txt

Create the autoland database:

    cd sql
    sudo -u postgres ./createdb.sh

Install and configure Apache (optional)

    sudo apt-get install apache2 libapache2-mod-wsgi
    sudo a2enmod headers
    sudo a2enmod wsgi
    sudo rm /etc/apache2/sites-enabled/000-default.conf
    sudo cp version-control-tools/apache/autoland-no-ssl.conf /etc/apache2/sites-enabled
    sudo apachectl restart

Create repositories

    sudo mkdir /repos
    sudo chmod 777 /repos
    cd /repos
    hg clone https://hg.mozilla.org/mozilla-central mozreview-gecko

Add the following to the mozreview-gecko .hgrc under paths:

    mozreview = http://reviewboard-hg.mozilla.org/gecko
    try = ssh://hg.mozilla.org/try

User account information and other configuration is expected to be found in
version-control-tools/autoland/autoland/config.json. A skeleton file used with
the docker image can be found in
version-control-tools/testing/docker/builder-autoland/config.json
and used as a basis for creating this file.


Testing
-------

The tests can be run by using the test script in the root version-control-tools
directory:

     run-mercurial-tests -j 2 autoland/tests

Mach commands are provided by the ottoland script in the root
version-control-tools directory that can be used for manual or automated tests.
The implementation of the commands is in
testing/vcttesting/autoland_mach_commands.py.
