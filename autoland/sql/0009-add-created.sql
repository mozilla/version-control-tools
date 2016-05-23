--This adds a created column to the transplant table so requests can be
--processed in the same order they were requested.
alter table transplant add column created timestamp not null default current_timestamp
