FROM secure:mozsecure:centos7:sha256 48cc2d545136115b38f38ee5f80d51db391fee2610f8300b280b35422db63af7:https://s3-us-west-2.amazonaws.com/moz-packages/docker-images/centos-7-20181101-docker.tar.xz

ENV RABBITMQ_CONFIG_FILE /etc/rabbitmq/rabbitmq

RUN yum update -y && yum install -y \
  https://github.com/rabbitmq/erlang-rpm/releases/download/v19.3.2/erlang-19.3.2-1.el7.centos.x86_64.rpm \
  https://github.com/rabbitmq/rabbitmq-server/releases/download/rabbitmq_v3_6_9/rabbitmq-server-3.6.9-1.el7.noarch.rpm && \
  yum clean all

ADD rabbitmq.config /etc/rabbitmq/rabbitmq.config
RUN chmod 644 /etc/rabbitmq/rabbitmq.config

RUN rabbitmq-plugins enable rabbitmq_management

EXPOSE 5672
EXPOSE 15672

CMD ["/usr/sbin/rabbitmq-server"]
