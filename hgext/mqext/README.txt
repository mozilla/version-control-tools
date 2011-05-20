Modify Mercurial's MQ extension by altering several commands and adding a few more. Install it by pointing your ~/.hgrc at it, eg:

  [extensions]
  mq =
  mqext = ~/lib/hg/mqext

Commands added:
  qshow - Display a single patch (similar to 'export')
  qexport - Write all patches to an output directory, with minor renaming
  qtouched - See what patches modify which files

Commands not related to mq:
  lineage - Dump out the revision history leading up to a particular revision

The following mq commands are modified to add options that autocommit any
changes made to your patch queue to the queue repository
(a la hg commit --mq):
  qrefresh
  qnew
  qrename
  qdelete

The expected usage is to add the 'mqcommit=auto' option to the 'mqext' section
of your ~/.hgrc so that all changes are autocommitted if you are using a
versioned patch queue, and to do nothing if not:

  [mqext]
  mqcommit = auto

You could also set it to 'yes' to force it to try to commit all changes, and
error out if you don't have (or have forgotten to create) a patch repository.
