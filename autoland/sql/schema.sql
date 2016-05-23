alter user autoland with password 'autoland';

create sequence request_sequence;
grant usage, select on sequence request_sequence to autoland;

create table Transplant (
    id bigint default nextval('request_sequence'),
    destination varchar(255),
    request json,
    landed boolean,
    result text,
    last_updated timestamp,
    created timestamp not null default current_timestamp,
    primary key(id)
);
grant all privileges on table Transplant to autoland;

create table MozreviewUpdate (
    id bigserial primary key,
    transplant_id bigint references transplant(id),
    data text
);
grant all privileges on table MozreviewUpdate to autoland;
grant usage, select on sequence mozreviewupdate_id_seq to autoland;
