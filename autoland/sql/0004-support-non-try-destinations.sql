--To support non-try destinations we need more space in the tree and destination
--columns. We'll also want to keep track of a push bookmark for repositories
--like version-control-tools where we push the bookmark @. See Bug 1128039.
alter table transplant alter column tree type varchar(255);
alter table transplant alter column destination type varchar(255);
alter table transplant add column push_bookmark varchar(255);
