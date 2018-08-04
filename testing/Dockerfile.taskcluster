FROM ubuntu:18.04

RUN groupadd -g 1000 worker && \
    useradd -u 1000 -g 1000 -s /bin/bash -m worker

# Set variable normally configured at login, by the shells parent process, these
# are taken from GNU su manual
ENV HOME=/home/worker \
    SHELL=/bin/bash \
    USER=worker \
    LOGNAME=worker \
    HOSTNAME=taskcluster-worker \
    DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
  apt-get install -y --no-install-recommends \
    autoconf \
    automake \
    build-essential \
    ca-certificates \
    gcc \
    gettext \
    git \
    libcurl4-openssl-dev \
    libffi-dev \
    liblzma-dev \
    libsasl2-dev \
    libldap2-dev \
    libssl-dev \
    libtool \
    npm \
    mercurial \
    pkg-config \
    python3 \
    python-dev \
    sqlite3 \
    zlib1g-dev && \
  apt-get clean -y && rm -rf /var/lib/apt/lists

RUN hg clone https://hg.mozilla.org/hgcustom/version-control-tools /vct-cache && \
  cd /vct-cache && \
  NO_DOCKER=1 ./create-test-environment && \
  chown -R worker:worker /vct-cache

# Install Watchman for fsmonitor tests
RUN git clone https://github.com/facebook/watchman.git /watchman && \
  cd /watchman && \
  git checkout v4.9.0 && \
  ./autogen.sh && \
  ./configure && \
  make && \
  make install

VOLUME /work
