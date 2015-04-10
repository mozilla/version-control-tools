# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# This container holds a copy of all vct data.

FROM ubuntu:14.04.2

RUN apt-get update && apt-get install -y rsync

VOLUME /vct-mount
ADD run.sh /run.sh

CMD ["/run.sh"]
