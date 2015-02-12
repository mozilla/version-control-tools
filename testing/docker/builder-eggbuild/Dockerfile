# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# This is a Docker container for building Python eggs required for
# Review Board / MozReview.

FROM centos:centos6

ENV DJBLETS_VERSION 0.8/Djblets-0.8.12-py2.6.egg
ENV REVIEWBOARD_VERSION 2.0/ReviewBoard-2.0.13-py2.6.egg
ENV DJANGO_EVOLUTION_VERSION 0.7/django_evolution-0.7.4-py2.6.egg

RUN yum install -y epel-release && yum update -y && \
    yum install -y gcc \
        nodejs npm uglify-js \
        python-pip python-setuptools python-virtualenv
RUN npm install -g less

RUN virtualenv /venv
RUN curl -sL -o /Djblets.egg https://downloads.reviewboard.org/releases/Djblets/${DJBLETS_VERSION}
RUN curl -sL -o /ReviewBoard.egg https://downloads.reviewboard.org/releases/ReviewBoard/${REVIEWBOARD_VERSION}
RUN curl -sL -o /django_evolution.egg https://downloads.reviewboard.org/releases/django-evolution/${DJANGO_EVOLUTION_VERSION}

ADD requirements.txt /requirements.txt
RUN /venv/bin/pip install -r /requirements.txt

RUN /venv/bin/easy_install /Djblets.egg
RUN /venv/bin/easy_install /django_evolution.egg
RUN /venv/bin/easy_install /ReviewBoard.egg

ADD eggserver.py /eggserver.py

ADD extra/vct /version-control-tools

ADD entrypoint.sh /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
EXPOSE 80
CMD ["/venv/bin/python", "/eggserver.py"]
