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

create table Testrun (\
    tree varchar(20),\
    revision varchar(40),\
    pending integer,\
    running integer,\
    builds integer,\
    can_be_landed boolean,\
    last_updated timestamp,\
    primary key(tree, revision)\
);
grant all privileges on table Testrun to autoland;

create table Transplant (\
    id bigint default nextval('request_sequence'),\
    tree varchar(20),\
    rev varchar(40),\
    destination varchar(20),\
    trysyntax text,\
    landed boolean,\
    result text,\
    review_updated boolean,\
    pingback_url text,\
    primary key(id)\
);
grant all privileges on table Transplant to autoland;
