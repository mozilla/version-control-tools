#! /bin/bash
set -e

function print_usage {
	cat <<USAGE_END
$0 [-s "source repo path or url"] -d "Destination repo" [-r "Revision"]

if -s is not specified, we use mozilla-central
if -r is not specified, we use tip
USAGE_END
}

REVISION=tip
TARGET=""
MIRRORS=/etc/mercurial/mirrors
PROJECTS=/repo/hg/mozilla/projects
SOURCE=/repo/hg/mozilla/mozilla-central

while getopts s:r:d: OPTION; do
	case $OPTION in
		s) SOURCE=${OPTARG}
			;;
		r) REVISION=${OPTARG}
			;;
		d) TARGET=${OPTARG}
			;;
		*) print_usage
		   exit
			;;
	esac
done

[ -z "$TARGET" ] && print_usage && exit 1

echo "Cloning revision ${REVISION} from ${SOURCE} to ${TARGET}"
echo "Deleting repo ${PROJECTS}/${TARGET}"
read -p "Proceed? (y/n): " ans
PROCEED="NO"
case $ans in
	y | yes)
	echo "Okay, here we go!"
	PROCEED="YES"
		;;
	n | no)
	PROCEED="NO"
	echo "Good choice, exiting."
	exit 0;
		;;
	*) 
	PROCEED="NO"
	echo "Did not understand response"
	exit 1;
		;;
esac

[ "${PROCEED}" == "YES" ] || exit 0

for hgweb in $(cat ${MIRRORS}); do ssh ${hgweb} "mv ${PROJECTS}/${TARGET} ${PROJECTS}/${TARGET}-old"; done

HGOPTS="--config hooks.changegroup.mirrorpush= --config hooks.changegroup.recordlogs="

cd ${PROJECTS} && mv ${TARGET} ${TARGET}-old
/var/hg/venv_tools/bin/hg ${HGOPTS} clone --pull -U ${SOURCE} ${TARGET}
cd ${PROJECTS}/${TARGET}/.hg

cat <<HGRC > ${PROJECTS}/${TARGET}/.hg/hgrc
[paths]
default = ${SOURCE}

[hooks]
pretxnchangegroup.a_treeclosure = python:mozhghooks.treeclosure.hook
changegroup.push_printurls = python:mozhghooks.push_printurls.hook
HGRC

echo "Setting permissions"
/var/hg/version-control-tools/scripts/repo-permissions ${PROJECTS}/${TARGET} hg scm_level_2 wwr

echo "Updating web heads"
(cd ${PROJECTS}/${TARGET} && /repo/hg/scripts/push-repo.sh)
(cd $repo && sudo -u hg /usr/local/bin/repo-push.sh $repo --hgrc)

echo "Clean up"
for hgweb in $(cat ${MIRRORS}); do ssh ${hgweb} "/bin/rm -r ${PROJECTS}/${TARGET}-old &"; done
wait
(cd ${PROJECTS} && rm -rf ${TARGET}-old)

echo "Done. Please ask buildduty in #releng to issue a no-op reconfig of the buildbot scheduler."
exit
