#!/bin/bash

OLDREPO=$(echo $1|sed 's/\/$//')
OWNER=$(stat -c %U $OLDREPO)
GROUP=$(stat -c %G $OLDREPO)
PERMS=$(stat -c %a $OLDREPO)
NEWREPO=$(echo $OLDREPO|sed 's/\/$//')-new

echo "Making new repo $NEWREPO"
mkdir $NEWREPO
pushd $NEWREPO > /dev/null
hg init
popd > /dev/null

echo "Pushing old repo $OLDREPO into new repo $NEWREPO"
pushd $OLDREPO > /dev/null
hg push $NEWREPO
popd > /dev/null

echo "Fixing owner and group"
chown -R $OWNER:$GROUP $NEWREPO
echo "Fixing permissions"
chmod -R $PERMS $NEWREPO

echo "Copying old hgrc to new repo"
cp ${OLDREPO}/.hg/hgrc ${NEWREPO}/.hg/

mkdir -p /repo/hg/dead_repositories/pushlog-restore/${OLDREPO}
echo "Moving old repository to /repo/hg/dead_repositories/pushlog-restore/${OLDREPO}"
mv $OLDREPO /repo/hg/dead_repositories/pushlog-restore/${OLDREPO}

echo "Moving new repository to ${OLDREPO}"
mv $NEWREPO $OLDREPO
