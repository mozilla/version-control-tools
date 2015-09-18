--This adds a last_updated column to the transplant table so we can be more
--intelligent about retrying things. See Bug 1203100.
alter table transplant add column last_updated timestamp;
