FROM secure:mozsecure:centos7:sha256 9f2f77ffd1614d29e5cc403c677eb726ede859f78e16017d608593cbbc3f0d2e:https://s3-us-west-2.amazonaws.com/moz-packages/docker-images/centos-7-20171101-docker.tar.xz

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
