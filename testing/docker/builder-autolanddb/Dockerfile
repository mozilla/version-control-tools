# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# This is a docker container for running a postgres server suitable for
# powering a autoland instance.

FROM postgres:9.5.0

# override this variable to store data inside the container rather than on a
# mounted volume.
ENV PGDATA /postgresql-data
RUN mkdir $PGDATA

# use autoland as default database
ENV POSTGRES_DB autoland

# %include autoland/sql/schema.sql
ADD extra/vct/autoland/sql/schema.sql /docker-entrypoint-initdb.d/schema.sql
ADD createdb.sql /docker-entrypoint-initdb.d/createdb.sql
