# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# This is a docker container for running a MySQL server suitable for
# powering a bugzilla.mozilla.org (BMO) instance. The container is
# pretty basic. It simply applies a custom MySQL configuration on top
# of the Docker-provided standard MySQL container.

FROM mysql:5.6.20

COPY my.cnf /etc/mysql/my.cnf
