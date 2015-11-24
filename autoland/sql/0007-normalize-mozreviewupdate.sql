-- This normalizes the mozreviewupdate table by removing the duplicated
-- pingback_url column. We drop the existing primary key constraint as we
-- might have more than one update for a transplant request and add a new id
-- column as well as a foreign key constraint on transplant instead.
-- See Bug 1225793.
alter table mozreviewupdate drop column pingback_url;
alter table mozreviewupdate drop constraint mozreviewupdate_pkey;
alter table mozreviewupdate add column id bigserial primary key;
alter table mozreviewupdate rename column request_id to transplant_id;
alter table mozreviewupdate add foreign key(transplant_id) references transplant(id);
grant usage, select on sequence mozreviewupdate_id_seq to autoland;
