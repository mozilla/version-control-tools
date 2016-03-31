#!/bin/bash
# script to pull list of repos from hg-push.log and compare revisions between
# hgssh1 and hgweb*

usage() {
    echo "Usage: $0 <string>" 1>&2
    echo "<string> is passed to awk as a regexp to search logs"
    echo "examples:"
    echo "$0 'Jul 22'               # all repos on July 22nd"
    echo "$0 'Jul 22.*try           # all try repos on July 22nd"
    echo "$0 'jhopkins@mozilla.com' # all repos pushed to by user (unbounded time)"
    exit 1
}

if [[ -z "$1" || ($1 == "-h") || ($1 == "--help") ]]; then
    usage
else
    search=$1
fi

hglog=/var/log/hg-push.log
mirrors=$(cat /etc/mercurial/mirrors)
hgcmd="hg log --limit 1 --template 'changeset: {node}' 2>/dev/null"
#hgcmd="hg tip --template 'changeset: {node}' 2>/dev/null"

workdir=$(mktemp -d)
list=${workdir}/list
revs=${workdir}/revs

echo "Output in ${workdir}"

# generate list of repos
/bin/awk '/'"${search}"'/ {print $10}' ${hglog} | /bin/sort -u > ${list}

# create script to generate repo rev data
cat > ${workdir}/listrevs.sh <<EOF
#!/bin/bash
root=/repo/hg/mozilla
workdir=${workdir}
list=${list}
rev=${revs}
pushd() { builtin pushd \$1 > /dev/null; }
popd()  { builtin popd \$1 > /dev/null; }
for repo in \$(cat ${list})
do
    pushd \${root}/\${repo} && echo "\${PWD/\/repo\/hg\/mozilla\/} \$(${hgcmd})" >> ${revs} && popd
done
EOF
chmod 700 ${workdir}/listrevs.sh

# sync list, script to mirrors
for host in ${mirrors}; do scp -qpr ${workdir} root@${host}:/tmp; done

# generate latest rev info per repo
${workdir}/listrevs.sh

for host in ${mirrors}
do
    ssh ${host} ${workdir}/listrevs.sh &
done
wait

# copy rev data back, clean up, and compare
for host in ${mirrors}; do scp -q ${host}:${revs} ${workdir}/revs.${host}; done
for host in ${mirrors}; do ssh root@${host} "/bin/rm -r ${workdir}"; done
for host in ${mirrors}
do
    echo -n "${host}: "
    diff ${revs} ${revs}.${host} && echo "up to date!"
done


