# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

FROM buildpack-deps:latest

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -yq \
    docker \
    docker-compose \
    libldap2-dev \
    libsasl2-dev \
    libssl-dev \
    python3 \
    python3-dev \
    python3-pip \
    python3-venv \
    python3-wheel \
    rsync \
    sqlite3

ARG USER_ID
ARG GROUP_ID
ARG DOCKER_GID
RUN echo 'EXTRA_GROUPS="docker host-docker"' >> /etc/adduser.conf
RUN addgroup --gid ${GROUP_ID} vct \
    && addgroup --gid ${DOCKER_GID} host-docker \
    && adduser \
        --disabled-password \
        --uid ${USER_ID} \
        --gid ${GROUP_ID} \
        --add_extra_groups \
        --home /vct \
        --gecos "vct,,," \
        vct

RUN mkdir /app
RUN chown -R vct:vct /app


# For testing older versions of Mercurial against Python 3
# TODO remove once Mercurial 5.1 is not supported
ENV HGPYTHON3=1

# Create Python 3 venv
# Set `VIRTUAL_ENV` and `PATH` to replicate `source venv/bin/activate`
# Install `wheel` since it seems to be missing
ENV VIRTUAL_ENV=/app/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN pip install --upgrade pip
RUN pip install wheel


# Install requirements for testing
# Use /app as the workdir to the installed .egg-info
# isn't mounted over by docker-compose
ADD test-requirements-3.txt /requirements.txt
WORKDIR /app
RUN pip install \
    --upgrade \
    --force-reinstall \
    --require-hashes \
    -r /requirements.txt


ADD ./ /app/vct/
RUN chown -R vct:vct /app

USER vct

# Install editable requirements py2/py3
RUN pip install -e vct/pylib/Bugsy
RUN pip install -e vct/pylib/mozansible
RUN pip install -e vct/pylib/mozhg
RUN pip install -e vct/pylib/mozhginfo
RUN pip install -e vct/pylib/mozautomation
RUN pip install -e vct/hgserver/hgmolib
RUN pip install -e vct/pylib/vcsreplicator
RUN pip install -e vct/hghooks
RUN pip install -e vct/testing

# clone cinnabar for the `cinnabarclone` extension
RUN git clone \
    --branch release \
    https://github.com/glandium/git-cinnabar.git /app/venv/git-cinnabar
WORKDIR /app/vct

# Install Mercurials
RUN python -m vcttesting.environment install-mercurials 3

VOLUME /app/vct

CMD ["sh"]
