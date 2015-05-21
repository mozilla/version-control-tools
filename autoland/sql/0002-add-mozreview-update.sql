
-- we now keep pending updates in MozreviewUpdate so we don't need to keep
-- track of whether we've updated Mozreview inside the Transplant table itself.
alter table Transplant drop column review_updated;

create table MozreviewUpdate (
    request_id bigint,
    pingback_url text,
    data text,
    primary key(request_id)
);
grant all privileges on table MozreviewUpdate to autoland;
