FROM centos:centos7

ENV RABBITMQ_CONFIG_FILE /etc/rabbitmq/rabbitmq

RUN sed -i 's/^mirrorlist/#&/;s,^#baseurl=http://mirror.centos.org,baseurl=http://vault.centos.org,' /etc/yum.repos.d/CentOS-Base.repo

RUN yum update -y && yum install -y \
  https://github.com/rabbitmq/erlang-rpm/releases/download/v19.3.2/erlang-19.3.2-1.el7.centos.x86_64.rpm \
  https://github.com/rabbitmq/rabbitmq-server/releases/download/rabbitmq_v3_6_9/rabbitmq-server-3.6.9-1.el7.noarch.rpm && \
  yum clean all

ADD testing/docker/builder-pulse/rabbitmq.config /etc/rabbitmq/rabbitmq.config
RUN chmod 644 /etc/rabbitmq/rabbitmq.config

RUN rabbitmq-plugins enable rabbitmq_management

EXPOSE 5672
EXPOSE 15672

CMD ["/usr/sbin/rabbitmq-server"]
