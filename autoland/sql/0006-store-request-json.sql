-- This adds a column for storing the request json and drops the columns for
-- the individual json fields. See Bug 1216947.
alter table transplant add column request json;
alter table transplant drop column tree;
alter table transplant drop column rev;
alter table transplant drop column trysyntax;
alter table transplant drop column push_bookmark;
alter table transplant drop column pingback_url;
