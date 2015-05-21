-- create a sequence which we can share between Transplant
-- and MozreviewPullRequest. We'll start numbering with the next value from
-- the current transplant id sequence.
create sequence request_sequence;
grant usage, select on sequence request_sequence to autoland;
select setval('request_sequence', (select nextval('transplant_id_seq')));

-- change transplant to use the new sequence
alter TABLE Transplant alter column id set default nextval('request_sequence');
drop sequence transplant_id_seq;

-- and finally create a table for pullrequests
create table MozreviewPullRequest (
    id bigint default nextval('request_sequence'),
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
