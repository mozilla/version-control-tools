# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# The container is similar to bmodb, but it stores its data in the local
# image, not in a volume. This is necessary to work around a bug in
# volume garbage collection in Docker where the old volumes don't get
# deleted on container deletion.

FROM mysql:5.6.20

COPY my.cnf /etc/mysql/my.cnf
