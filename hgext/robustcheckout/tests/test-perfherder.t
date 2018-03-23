  $ . $TESTDIR/hgext/robustcheckout/tests/helpers.sh
  $ export TASKCLUSTER_INSTANCE_TYPE=c5.4xlarge

  $ hg robustcheckout http://localhost:$HGPORT/repo0 dest --revision 5d6cdc75a09b
  (using Mercurial 4.2.3)
  ensuring http://localhost:$HGPORT/repo0@5d6cdc75a09b is available at dest
  (sharing from new pooled repository b8b78f0253d822e33ba652fd3d80a5c0837cfdf3)
  requesting all changes
  adding changesets
  adding manifests
  adding file changes
  added 3 changesets with 3 changes to 1 files (+1 heads)
  searching for changes
  no changes found
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  updated to 5d6cdc75a09bcccf76f9339a28e1d89360c59dce
  PERFHERDER_DATA: {"framework": {"name": "vcs"}, "suites": \[{"extraOptions": \["c5.4xlarge"\], "lowerIsBetter": true, "name": "clone", "shouldAlert": false, "subtests": \[\], "value": \d+\.\d+}, {"extraOptions": \["c5\.4xlarge"\], "lowerIsBetter": true, "name": "update", "shouldAlert": false, "subtests": \[\], "value": \d+\.\d+}, {"extraOptions": \["c5.4xlarge"\], "lowerIsBetter": true, "name": "overall", "shouldAlert": false, "subtests": \[\], "value": \d+\.\d+}]} (re)
