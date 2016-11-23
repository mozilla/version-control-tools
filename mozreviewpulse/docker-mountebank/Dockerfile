FROM node:alpine

MAINTAINER Māris Fogels <mars@mozilla.com>

ENV MOUNTEBANK_MAJOR_VERSION 1.6
ENV MOUNTEBANK_VERSION 1.6.0
ENV MOUNTEBANK_SHA256 0149ee5c1a7f1f02e0a46e748d16a7a8c7145c459139357e6f73e39f0e716308

# So wget works over SSL
RUN apk --no-cache add openssl

# Install the mountebank nodejs service. See http://www.mbtest.org/docs/install
RUN wget -c -O mountebank.tar.gz https://s3.amazonaws.com/mountebank/v${MOUNTEBANK_MAJOR_VERSION}/mountebank-v${MOUNTEBANK_VERSION}-npm.tar.gz \
    && echo "${MOUNTEBANK_SHA256}  mountebank.tar.gz" | sha256sum -c \
    && tar xf mountebank.tar.gz \
    && rm mountebank.tar.gz

EXPOSE 2525

ENTRYPOINT ["/mountebank/bin/mb"]
CMD ["--help"]
