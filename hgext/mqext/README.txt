Modify Mercurial's MQ extension by altering several commands and adding a few more. Install it by pointing your ~/.hgrc at it, eg::

  [extensions]
  mq =
  mqext = ~/lib/hg/mqext

Commands added:

  :qshow: Display a single patch (similar to 'export')
  :qexport: Write all patches to an output directory, with minor renaming
  :qtouched: See what patches modify which files

Commands not related to mq:

  :lineage: Dump out the revision history leading up to a particular revision
  :reviewers: Suggest potential reviewers for a patch

Autocommit:

If you would like to have any change to your patch repository committed to
revision control, mqext adds -Q and -M flags to all mq commands that modify the
patch repository. -Q commits the change to the patch repository, and -M sets
the log message used for that commit (but mqext provides reasonable default
messages, tailored to the specific patch repo-modifying command, so you'll
rarely use this.)

The following commands are modified:

  - qrefresh
  - qnew
  - qrename
  - qdelete
  - qimport
  - qfinish

The expected usage is to add the 'mqcommit=auto' option to the 'mqext' section
of your ~/.hgrc so that all changes are autocommitted if you are using a
versioned patch queue, and to do nothing if not::

  [mqext]
  mqcommit = auto

You could also set it to 'yes' to force it to try to commit all changes, and
error out if you don't have (or have forgotten to create) a patch repository.

Alternatively, if you only want a subset of commands to autocommit, you may add
the -Q option to all relevant commands in your ~/.hgrc::

  [defaults]
  qnew = -Q
  qdelete = -Q
  qimport = -Q
