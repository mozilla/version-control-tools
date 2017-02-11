.. _vcssync_servo:

========================
Servo Repository Syncing
========================

Aspects of development on the `Servo <https://github.com/servo/servo>`_
and Firefox/Gecko web platforms are closely related, with some
components shared between the two projects. Developers often want to
make changes for and test against both projects at once. For this
reason, Mozilla has an automated mechanism for *synchronizing* the
two code repositories.

Architecture
============

.. note::

   This section details the architecture as it is implemented today. It does
   not (yet) detail the final, planned architecture.

Servo is canonically developed on GitHub using the Git version control tool.
Servo makes heavy use of the GitHub workflow receiving changes (*Pull
Requests*). When a Git branch is accepted, it is merged into the *master*
branch of the Servo Git repository.

Firefox is canonically developed on hg.mozilla.org using the Mercurial
version control tool. There are multiple repositories that are periodically
merged into one another.

The commit history of the Servo projected is *vendored* into the *servo/*
directory of the Firefox Mercurial repository. The mechanism by which this
happens is roughly as follows:

1. Git commits are normalized to provide a sanitized, suitable-for-Firefox
   representation of history.
2. The rewritten Git commits are converted to Mercurial changesets.
3. The Mercurial changesets are essentially replayed onto the Firefox
   repository into the *servo/* directory.

Git History Rewriting
---------------------

Before Servo's history is converted to Mercurial, it goes through a significant
rewriting and normalization process. The following transforms are performed:

* Merge commits are removed, leaving only the first-parent ancestry (commits
  on non-first-parent DAG branches tend to not be very useful in the context
  of Firefox and pollute the history of Firefox, which tries to not use merge
  commits).
* Certain directories (like web platform tests) are removed from history
  because they are large and/or redundant with files already in the Firefox
  repo.
* Non-useful annotations from commit messages (such as the boilerplate markdown
  for reviewable.io) are removed.
* The commit message summary line is prefixed with ``servo:`` and contains
  the GitHub pull request number, title and source (data obtained from GitHub
  API).
* The Git committer field is set to the value of the author field.
* Annotations to the commit's original source URL and revision are added to
  the commit message.

The end result is a Git head with 100% linear history (no merge commits) and
consistently formatted commit messages.

Mercurial Conversion
--------------------

The rewritten Git history is converted to a Mercurial repository using
``hg convert``. As part of the conversion:

* All data related to Git submodules is dropped (Servo stopped using
  submodules in 2015).
* Aggressive copy detection is performed matching at 75% similarly.

Repository Overlay into Firefox
-------------------------------

After the rewritten Servo repository is converted to Mercurial, the next
step is to incorporate those changesets into the Firefox repository.

This is accomplished through a process called *overlaying*. Essentially,
this process builds a list of files (*manifest* in Mercurial terminology)
that is a union of files in the Firefox and Servo repositories, prefixing
files from the Servo repository with the path ``servo/``. A changeset
copying details from the corresponding source changeset is committed. This
result looks like someone took all the diffs from the Mercurial Servo
repository and applied them to the Firefox repository.

Operational Guide
=================

The processes for converting the Servo repository and overlaying it into
the Firefox repository live on a *vcs-sync* server. The processes are
largely stateless. All that's needed to run an instance (beside the code
of course) are some credentials to access various authenticated services.

The service configuration lives in the ``vcs-sync`` Ansible role in the
version-control-tools repository. There is a standalone ``servo-sync.yml``
playbook for configuring just the Servo pieces.

The logical service is composed of multiple systemd services and related
units, each responsible for one part of the pipeline.

servo-linearize.service
-----------------------

The ``servo-linearize.service`` systemd service is responsible for rewriting
Git history and converting it to Mercurial.

This one-shot service runs in response to a detected push to the Servo Git
repository and periodically via a timer (``servo-linearize.timer``).

When executed, this process:

1. Fetches changes from the Servo Git repository to a local clone.
2. Rewrites any Git commits from the origin that haven't already been
   rewritten.
3. Mirrors the Git repo (contains original and converted refs/heads) to
   https://github.com/mozilla/converted-servo.
4. Converts any unconverted Git commits to Mercurial changesets
5. Pushes the Mercurial repository to
   https://hg.mozilla.org/projects/converted-servo-linear
6. Exits.

The service should be safe to run at any time. If there is no work to do,
it no-ops.

servo-overlay.service
---------------------

The ``servo-overlay.service`` systemd service is responsible for overlaying
the Mercurial Servo repository onto a Firefox repository. This one-shot service
runs in response to a detected push to the Mercurial Servo repository
and periodically via a timer (``servo-overlay.timer``).

When executed, this process:

1. Pulls the latest revision of the Firefox Mercurial repository onto
   which changesets should be based.
2. Pulls the Mercurial Servo repository.
3. Finds changesets from the Mercurial Servo repository not yet applied
   in the Firefox repository.
4. Overlays each Servo changeset into the Firefox repository until done.
5. Attempts to push the result.

The service should be safe to run at any time. If there is no work to do, it
no-ops.

In some situations, the operation may fail. For example, the Firefox repository
is closed and pushes aren't being allowed. When this happens, a subsequent
invocation will delete what was left over from the previous failed attempt
and redo the process.

servo-pulse-monitor.service
---------------------------

The ``servo-pulse-monitor.service`` systemd service is a daemon that subscribes
to Pulse notifications for hg.mozilla.org and GitHub. When it sees a push to
the Servo Git repository, it starts ``servo-linearize.service``. When it sees
a push to the ``converted-servo-linear`` Mercurial repository, it starts
``servo-overlay.service``.

The purpose of the Pulse monitor daemon is to react to repository change
events with minimal delay. This allows commits to be *synchronized* from
Servo to Firefox in a matter of seconds. This is both faster and more
efficient than polling servers for activity.

Neither Pulse nor GitHub have highly robust delivery guarantees. So it is
possible change notification messages may be lost. For this reason, systemd
timers periodically trigger ``servo-linearize.service`` and
``servo-overlay.service``. In the event of a Pulse notification failure,
the maximum time to handle is effectively capped at the period of these
timers (as opposed to when the next Pulse notification is delivered - which
could be hours or more).

servo-sync.target
-----------------

For convenience, the ``servo-sync.target`` systemd unit can be used to
start and stop all services associated with Servo VCS syncing.

Provisioning a New Instance
===========================

The Servo VCS Syncing *appliance* can be provisioned in a relatively
turn-key manner. Generally speaking, it should be safe to destroy the
existing instance and provision a new one at any time.

The EC2 instance and other supporting AWS infrastructure is managed by
Terraform. From the ``devservices-aws`` Git repo, go to the
``vcssync`` directory and run ``terraform plan`` then ``terraform apply``
if the proposed changed check out.

After a minute or two, you should be able to SSH into
``servo-vcs-sync.mozops.net`` via the bastion host in us-west-2.

.. note::

   The instance reboots after initialization to apply any system package
   updates that may require a reboot.

Once you have a fresh instance, you'll need to provision it.

The first step is to install the secrets on the host. These include
SSH keys, passwords, and other tokens. The secrets file is encrypted
in a *vault*. Have a friendly Ops friend decrypt the file then
run ``ansible-playbook -i hosts vcssync-seed-secrets.yml`` from
``ansible/`` in ``version-control-tools``. This will copy the
secrets file to the host.

Once the secrets file is in place on the server, Ansible can do the
reset. From ``version-control-tools``::

   $ ./deploy vcs-sync

This will take a while on initial provision because it needs to install
system packages, Python virtualenvs, and pre-clone various repositories.
