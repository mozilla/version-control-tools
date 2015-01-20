FROM ubuntu:14.04.1

ENV RABBITMQ_CONFIG_FILE /etc/rabbitmq/rabbitmq

RUN apt-get update && apt-get -y install rabbitmq-server

ADD rabbitmq.config /etc/rabbitmq/rabbitmq.config

RUN rabbitmq-plugins enable rabbitmq_management

EXPOSE 5672
EXPOSE 15672

CMD ["/usr/sbin/rabbitmq-server"]
