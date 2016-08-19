# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# This container holds a copy of all vct data.

FROM secure:mozsecure:ubuntu1604:sha256 90243b2f486d1c6ca0c1e6649da940eb499759c4dad28bc831299df1ccef4e80:https://s3-us-west-2.amazonaws.com/moz-packages/docker-images/ubuntu-1604-20160818-docker.tar.xz

RUN apt-get update && apt-get install -y rsync

VOLUME /vct-mount
ADD run.sh /run.sh

CMD ["/run.sh"]
