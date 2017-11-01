# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# Builds a Python chroot suitable for hgweb.

FROM secure:mozsecure:centos7:sha256 9f2f77ffd1614d29e5cc403c677eb726ede859f78e16017d608593cbbc3f0d2e:https://s3-us-west-2.amazonaws.com/moz-packages/docker-images/centos-7-20171101-docker.tar.xz

RUN yum update -y

# Install build dependencies.
RUN yum install -y bzip2-devel gcc libcap-devel libcgroup-devel make openssl-devel rsync sqlite-devel tar wget zlib-devel

# Download and verify Python source code.
RUN wget https://www.python.org/ftp/python/2.7.12/Python-2.7.12.tgz
ADD Python-2.7.12.tgz.asc /Python-2.7.12.tgz.asc
ADD signer.gpg /signer.gpg
RUN gpg --import /signer.gpg
RUN gpg --verify /Python-2.7.12.tgz.asc

# Compile and install Python into a directory that will become the
# chroot.
RUN tar -xzf /Python-2.7.12.tgz
RUN cd /Python-2.7.12 && ./configure --prefix=/usr && make -j4 && make install DESTDIR=/python

# %include scripts/download-verify
ADD extra/vct/scripts/download-verify /var/tmp/download-verify

# Install pip
RUN /var/tmp/download-verify https://s3-us-west-2.amazonaws.com/moz-packages/setuptools-20.1.1.tar.gz \
      /var/tmp/setuptools-20.1.1.tar.gz \
      2663ce0b0e742ee27c3a06b2da14563e4f6f713eaf5509b932a31793f9dea9a3 && \
    cd /var/tmp && tar -xzf setuptools-20.1.1.tar.gz && \
    cd /var/tmp/setuptools-20.1.1 && /python/usr/bin/python setup.py install

RUN /var/tmp/download-verify https://s3-us-west-2.amazonaws.com/moz-packages/pip-8.0.3.tar.gz \
      /var/tmp/pip-8.0.3.tar.gz \
      30f98b66f3fe1069c529a491597d34a1c224a68640c82caf2ade5f88aa1405e8 && \
    cd /var/tmp && tar -xzf pip-8.0.3.tar.gz && \
    cd /var/tmp/pip-8.0.3 && /python/usr/bin/python setup.py install

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
       /lib64/liblzma.so.5 \
       /lib64/libm.so.6 \
       /lib64/libpcre.so.1 \
       /lib64/libpthread.so.0 \
       /lib64/libresolv.so.2 \
       /lib64/libselinux.so.1 \
       /lib64/libsqlite3.so.0 \
       /lib64/libutil.so.1 \
       /lib64/libz.so.1 \
       /python/lib64/
RUN cp /usr/lib64/libssl.so.10 \
       /usr/lib64/libcrypto.so.10 \
       /python/usr/lib64/

# Install packages in virtualenv.
ADD requirements.txt /requirements.txt
RUN /python/usr/bin/python /python/usr/bin/pip install --require-hashes -r /requirements.txt

# Add additional support files and paths.
ADD hgrc /python/etc/mercurial/hgrc
RUN mkdir /python/repo_local
RUN ln -s /repo/hg /python/repo_local/mozilla

# Compile our executor program.
ADD mozbuild-eval.c /mozbuild-eval.c
RUN gcc -Wall -Wextra -Werror -o /mozbuild-eval -lcgroup /mozbuild-eval.c

ADD bootstrap /bootstrap
CMD ["/bootstrap"]
