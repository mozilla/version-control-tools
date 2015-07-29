# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# Builds a Python chroot suitable for hgweb.

FROM secure:mozsecure:centos6:sha256 88cc1475bd58f6ff6f41d50b813c9998c4d3a7167a8a45f8bd0b4a8342dec0db:https://s3-us-west-2.amazonaws.com/moz-packages/docker-images/centos-6-20150615_2019-docker.tar.xz

# Install build dependencies.
RUN yum install -y bzip2-devel gcc libcgroup-devel make openssl-devel rsync tar wget zlib-devel

# Download and verify Python source code.
RUN wget https://www.python.org/ftp/python/2.7.10/Python-2.7.10.tgz
ADD Python-2.7.10.tgz.asc /Python-2.7.10.tgz.asc
ADD signer.gpg /signer.gpg
RUN gpg --import /signer.gpg
RUN gpg --verify /Python-2.7.10.tgz.asc

# Compile and install Python into a directory that will become the
# chroot.
RUN tar -xzf /Python-2.7.10.tgz
RUN cd /Python-2.7.10 && ./configure --prefix=/usr && make -j4 && make install DESTDIR=/python

# Install pip
RUN /python/usr/bin/python -m ensurepip

# Copy library dependencies.
RUN mkdir -p /python/lib64 /python/usr/lib64
RUN cp \
       /lib64/ld-linux-x86-64.so.2 \
       /lib64/libbz2.so.1 \
       /lib64/libc.so.6 \
       /lib64/libcom_err.so.2 \
       /lib64/libdl.so.2 \
       /lib64/libgssapi_krb5.so.2 \
       /lib64/libk5crypto.so.3 \
       /lib64/libkeyutils.so.1 \
       /lib64/libkrb5.so.3 \
       /lib64/libkrb5support.so.0 \
       /lib64/libm.so.6 \
       /lib64/libpthread.so.0 \
       /lib64/libresolv.so.2 \
       /lib64/libselinux.so.1 \
       /lib64/libutil.so.1 \
       /lib64/libz.so.1 \
       /python/lib64/
RUN cp /usr/lib64/libssl.so.10 \
       /usr/lib64/libcrypto.so.10 \
       /python/usr/lib64/

# Install peep
# %include ansible/files/peep.py
ADD extra/vct/ansible/files/peep.py /python/usr/bin/peep.py

# Install packages in virtualenv.
ADD requirements.txt /requirements.txt
RUN /python/usr/bin/python /python/usr/bin/peep.py install -r /requirements.txt

# Add additional support files and paths.
ADD hgrc /python/etc/mercurial/hgrc
RUN mkdir /python/repo_local
RUN ln -s /repo/hg /python/repo_local/mozilla

# Compile our executor program.
ADD mozbuild-eval.c /mozbuild-eval.c
RUN gcc -Wall -Wextra -Werror -o /mozbuild-eval -lcgroup /mozbuild-eval.c

ADD bootstrap /bootstrap
CMD ["/bootstrap"]
