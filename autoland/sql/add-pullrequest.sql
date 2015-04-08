create table MozreviewPullRequest (
    id bigserial,
    ghuser varchar(255),
    repo varchar(255),
    pullrequest integer,
    destination varchar(20),
    bzuserid integer,
    bzcookie varchar(255),
    bugid integer,
    landed boolean,
    result text,
    pullrequest_updated boolean,
    pingback_url text,
    primary key(id)
);
grant all privileges on table MozreviewPullRequest to autoland;
grant usage, select on sequence mozreviewpullrequest_id_seq to autoland;
