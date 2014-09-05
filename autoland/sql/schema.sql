drop role if exists autoland;
create user autoland password 'autoland';

create table AutolandRequest (
    tree varchar(20),
    revision varchar(40),
    bugnumber integer,
    patch text,
    pending integer,
    running integer,
    builds integer,
    last_updated timestamp,
    can_be_landed boolean,
    landed boolean,
    primary key(tree, revision)
);
grant all privileges on table AutolandRequest to autoland;
