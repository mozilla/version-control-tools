FROM rockylinux:8

ENV RABBITMQ_CONFIG_FILE /etc/rabbitmq/rabbitmq

RUN yum update -y && yum install -y \
  https://github.com/rabbitmq/erlang-rpm/releases/download/v26.2.5/erlang-26.2.5-1.el8.x86_64.rpm \
  https://github.com/rabbitmq/rabbitmq-server/releases/download/v3.13.3/rabbitmq-server-3.13.3-1.el8.noarch.rpm && \
  yum clean all

ADD testing/docker/builder-pulse/rabbitmq.config /etc/rabbitmq/rabbitmq.config
RUN chmod 644 /etc/rabbitmq/rabbitmq.config

RUN rabbitmq-plugins enable rabbitmq_management

EXPOSE 5672
EXPOSE 15672

CMD ["/usr/sbin/rabbitmq-server"]
