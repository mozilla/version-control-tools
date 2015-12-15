pylintconfig() {
   cat > pylintbot.ini << EOF
[pulse]
host = ${PULSE_HOST}
port = ${PULSE_PORT}
userid = guest
password = guest
exchange = exchange/mozreview/
queue = all
ssl = False
routing_key = #
timeout = 60.0
[reviewboard]
url = ${REVIEWBOARD_URL}
user = pylintbot@example.com
password = password
[hg]
repo_root = `pwd`/repos
EOF
}

pylintsetup() {
  pylintconfig $1

  mozreview create-user pylintbot@example.com password 'Pylintbot :pylintbot' --bugzilla-group editbugs --uid 2000 --scm-level 3 > /dev/null

  cd client
  echo foo0 > foo
  hg commit -A -m 'root commit' > /dev/null
  hg phase --public -r .
  hg push --noreview > /dev/null
}

eslintconfig() {
   cat > eslintbot.ini << EOF
[pulse]
host = ${PULSE_HOST}
port = ${PULSE_PORT}
userid = guest
password = guest
exchange = exchange/mozreview/
queue = all
ssl = False
routing_key = #
timeout = 60.0
[reviewboard]
url = ${REVIEWBOARD_URL}
user = eslintbot@example.com
password = password
[hg]
repo_root = `pwd`/repos
EOF
}

eslintsetup() {
  eslintconfig
  mozreview create-user eslintbot@example.com password 'ESLintBot :eslintbot' --bugzilla-group editbugs --uid 2000 --scm-level 3 > /dev/null
}