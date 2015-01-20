alter user autoland with password 'autoland';

create table Testrun (
    tree varchar(20),
    revision varchar(40),
    pending integer,
    running integer,
    builds integer,
    can_be_landed boolean,
    last_updated timestamp,
    primary key(tree, revision)
);
grant all privileges on table Testrun to autoland;

create table Transplant (
    id bigserial,
    tree varchar(20),
    rev varchar(40),
    destination varchar(20),
    trysyntax text,
    landed boolean,
    result text,
    review_request_id bigint,
    review_updated boolean,
    primary key(id)
);
grant all privileges on table Transplant to autoland;
grant usage, select on sequence transplant_id_seq to autoland;
