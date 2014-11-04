autoland
========

Overview
--------

Autoland is a tool to monitor patches submitted to the try server [1] and land
them automatically provided builds succeed and tests pass. It works closely
with the transplant tool [2] to accomplish this.

When pushing autoland patches to try it is necessary that the head patch be
empty and that the commit message contains the try syntax along with the
string '--autoland'.

An example of a summary for an autoland push is:

  * try: -b do -p all -u all -t none --autoland
  * Bug XXXXXX - Do interesting stuff; r=yyy

The autoland tool does not mandate a minimal set of tests for a change or
check that the patch has been properly reviewed. In order to keep autoland as
simple as possible it is assumed that these policies will be enforced elsewhere,
for instance, in mozreview [3]. A check is done to verify that the person who
pushed to try is a member of the appropriate LDAP group to land on the
destination repository, i.e. scm level 3 in order to land on mozilla-inbound.

A single failure is allowed for each build and test. In this case, autoland
automatically retriggers the job to see if it will succeed on the second
attempt. If it succeeds on the second run, it is assumed that the failure was
intermittent and that the patch can be landed. If two failures occur for any
build or test, the autoland request fails.

If the autoland request succeeds, the transplant tool is used to land the
changes. Whether or not the request succeeds, the bugzilla bug corresponding to
the request is updated.

[1] http://hg.mozilla.org/try/
[2] https://github.com/laggyluke/build-transplant
[3] http://mozilla-version-control-tools.readthedocs.org/en/latest/mozreview.html


Design
------

Conceptually autoland consists of four components: a pulse listener, a bugzilla
interface, a transplant interface, and autoland itself. For convenience,
the last three are currently combined within one python program, but they could
easily be split out if required.

The pulse listener listens for build and test _started_ and _finished_  messages
on Mozilla Pulse [1]. Commit comments for started builds are examined for the
'--autoland' string. If present, and the autoland request is not known to the
system, data about the commit is added to a postgres database. Both _started_
and _finished_ messages are used as a trigger to query the buildapi to determine
the number of pending, running and finished jobs for the changeset. This is
done to limit the amount of polling down by autoland.

The bugzilla interface posts comments to bugs when autoland requests succeed or
fail. Comments are stored in postgres until successfuly posted.

The transplant interface attempts to transplant changesets for successful
autoland requests. Again, the changesets are stored in postgres so the
transplant can be retried in the event the server is unavailable.

The main portion of autoland periodically checks the postgres database for
incomplete autoland jobs which have no pending or running builds or which have
not been examined recently (e.g. no activity in the past 30 minutes). The
buildapi is then used to determine whether or not the job has completed. If so,
it is examined to see if any failures have occurred. If there are no failures,
the request is marked as ready to be landed. If there are single failures for
any job types, requests are made to rebuild those jobs. If there are two
failures for any job types, the autoland request is marked as failed.

[1] https://pulse.mozilla.org/

Installation
------------

Install required ubuntu packages:

    sudo apt-get update
    sudo apt-get install git pip python-dev postgresql libqu-dev libldap2-dev libsasl2-dev

Create a virtualenv:

    sudo pip install virtualenv
    virtualenv venv
    . venv/bin/activate

Install python libs

    pip install -r requirements.txt

Create the autoland database:

    cd sql
    sudo -u postgres ./createdb.sh
