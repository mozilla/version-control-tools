alter user autoland with password 'autoland';

create sequence request_sequence;
grant usage, select on sequence request_sequence to autoland;

create table MozreviewPullRequest (\
    id bigint default nextval('request_sequence'),\
    ghuser varchar(255),\
    repo varchar(255),\
    pullrequest integer,\
    destination varchar(20),\
    bzuserid integer,\
    bzcookie varchar(255),\
    bugid integer,\
    landed boolean,\
    result text,\
    pullrequest_updated boolean,\
    pingback_url text,\
    primary key(id)\
);
grant all privileges on table MozreviewPullRequest to autoland;

create table Transplant (\
    id bigint default nextval('request_sequence'),\
    destination varchar(255),\
    request json,\
    landed boolean,\
    result text,\
    last_updated timestamp,\
    primary key(id)\
);
grant all privileges on table Transplant to autoland;

create table MozreviewUpdate (\
    request_id bigint,\
    pingback_url text,\
    data text,\
    primary key(request_id)\
);
grant all privileges on table MozreviewUpdate to autoland;
