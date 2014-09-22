alter user autoland with password 'autoland';

create table AutolandRequest (
    tree varchar(20),
    revision varchar(40),
    bugid integer,
    blame varchar(120),
    message text,
    pending integer,
    running integer,
    builds integer,
    last_updated timestamp,
    can_be_landed boolean,
    landed boolean,
    primary key(tree, revision)
);
grant all privileges on table AutolandRequest to autoland;

create table BugzillaComment (
    sequence bigserial,
    bugid integer,
    bug_comment text,
    primary key(sequence)
);
grant all privileges on table BugzillaComment to autoland;
grant usage, select on sequence bugzillacomment_sequence_seq to autoland;
