# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

FROM buildpack-deps:latest

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -yq \
    docker.io \
    docker-compose \
    libldap2-dev \
    libsasl2-dev \
    libssl-dev \
    python3-dev \
    rsync \
    sqlite3 \
    make \
    build-essential \
    libssl-dev \
    zlib1g-dev \
    libbz2-dev \
    libreadline-dev \
    libsqlite3-dev \
    wget \
    curl \
    llvm \
    libncurses5-dev \
    xz-utils \
    tk-dev \
    libxml2-dev \
    libxmlsec1-dev \
    libffi-dev \
    liblzma-dev

COPY --from=ghcr.io/astral-sh/uv:0.11.15 /uv /usr/local/bin/uv

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

USER vct

# Required to ensure built Python uses utf-8.
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8

ENV HOME="/vct"

# Create Python 3.9 venv with uv
# Set `VIRTUAL_ENV` and `PATH` to replicate `source venv/bin/activate`
ENV VIRTUAL_ENV=/app/venv
RUN uv venv $VIRTUAL_ENV --python 3.9.13
ENV PATH="$VIRTUAL_ENV/bin:$PATH"


# Install Mercurials early so this layer is cached independently of vct source changes.
ADD testing/vcttesting/install_mercurials.py /app/install_mercurials.py
RUN python /app/install_mercurials.py

# Install external test dependencies early for layer caching.
# Use /app/vct as workdir so uv finds pyproject.toml/uv.lock.
ADD pyproject.toml uv.lock /app/vct/
WORKDIR /app/vct
RUN uv sync --no-dev --group test --no-install-project --frozen

ADD --chown=vct ./ /app/vct/

# Install editable local packages.
RUN uv sync --no-dev --group test --group local-test --no-install-project --frozen

# clone cinnabar for the `cinnabarclone` extension
RUN git clone \
    --branch release \
    https://github.com/glandium/git-cinnabar.git /app/venv/git-cinnabar

VOLUME /app/vct

CMD ["sh"]
