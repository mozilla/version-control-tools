#!/bin/bash
#
# Creates clones for gaia-l10n, e.g. bug 948141, 1000962
# run as root
#
# Update hooks, if needed
# as root, mkdir ${DEST}/${VER} && chown hg:scm_level_3 ${DEST}/${VER}
#

MIRRORS=/etc/mercurial/mirrors
SRC=/repo/hg/mozilla/gaia-l10n
DEST=/repo/hg/mozilla/releases/gaia-l10n
WSGI=/repo/hg/webroot_wsgi/releases/gaia-l10n
venv=/repo/hg/venv_tools

usage() {
    echo "Usage: $0 [-cn] -v VERSION list of locales in quotes"
    echo "e.g.: $0 -v v1_4 ar as en-US ff nb-NO ru zh-TW"
    echo "use '-n' to create new source repo as well"
    exit
}

die() {
    echo "$1" 1>&2
    exit ${1:+1}
}

new_source_repo=false
while getopts v:n OPTION; do
    case $OPTION in
        v) VER=${OPTARG}
            ;;
        n) new_source_repo=true
            ;;
        *) usage
            ;;
    esac
done
shift $((OPTIND-1))

[ -z "${VER}" ] && usage
LOCALES="$@"
[ -z "${LOCALES}" ] && usage

if [ \! -d "${DEST}/${VER}" ]; then
  mkdir "${DEST}/${VER}" || die "can't make ${DEST}/${VER} ?!"
  chown hg:scm_level_3 "${DEST}/${VER}"
fi

basic_repo_setup() {
    local loc="$1"
    local -i ec=0
    cat <<EOF > ${loc}/.hg/hgrc
[hooks]
pretxnchangegroup.a_singlehead = python:mozhghooks.single_head_per_branch.hook
EOF
    ec=$?
    /repo/hg/version-control-tools/scripts/repo-permissions $loc hg scm_l10n wwr || ec=$?
    pushd ${loc} >/dev/null
    echo "Doing initial push to webheads for ${loc}"
    /repo/hg/scripts/push-repo.sh || ec=$?
    sudo -u hg /usr/local/bin/repo-push.sh ${loc} --hgrc
    popd >/dev/null
    test ${ec} -eq 0 ||
        die "Can't do basic setup '${loc}' (${ec})"
}

cd ${DEST}/${VER}
echo `pwd`
for loc in $LOCALES; do
    if ! test -d ${SRC}/${loc}; then
        ${new_source_repo} || die "Missing SRC repo for locale '${loc}'"
        ( # push subshell to avoid cwd concerns
            cd ${SRC} || die "Can't cd to '${SRC}' ($?)"
            su hg -c "$venv/bin/hg init ${loc}" || die "Can't 'hg init ${loc}' ($?)"
            basic_repo_setup "${loc}" ||
            chown hg ${loc}/.hg/hgrc ||
                die "Can't chown hg ${loc}/.hg/hgrc ($?)"
        )
    fi
    su hg -c "$venv/bin/hg clone -v --time -U ${SRC}/${loc} ${loc}"
    basic_repo_setup "${loc}"
done

echo "Don't forget to update the gitweb_mozilla index.tmpl and wsgi files for the new version!"
echo "Both are done in v-c-t"
exit
