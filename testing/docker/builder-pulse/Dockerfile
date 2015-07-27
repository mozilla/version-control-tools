FROM secure:mozsecure:ubuntu14042:sha256 e08475e91c8b342dce147346a11db16357619ed914aaad4d82be2e6ab743a167:https://s3-us-west-2.amazonaws.com/moz-packages/docker-images/ubuntu-trusty-core-cloudimg-amd64-docker-20150630.tar.xz

ENV RABBITMQ_CONFIG_FILE /etc/rabbitmq/rabbitmq

RUN apt-get update && apt-get --no-install-recommends -y install rabbitmq-server

ADD rabbitmq.config /etc/rabbitmq/rabbitmq.config

RUN rabbitmq-plugins enable rabbitmq_management

EXPOSE 5672
EXPOSE 15672

CMD ["/usr/sbin/rabbitmq-server"]
