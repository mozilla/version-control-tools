/*

This file contains code to turn a vanilla Bugzilla database into something
that more resembles BMO.

Ideally it would contain a dump of the important data from BMO. Until then,
we populate a few key items.

*/

/* review flag */
INSERT INTO `flagtypes` (name, description, target_type, is_active, is_requestable, is_requesteeble, is_multiplicable, sortkey) VALUES ('review', 'request review', 'a', 1, 1, 1, 1, 1);

INSERT INTO `flaginclusions` (type_id, product_id, component_id) VALUES (2, 1, 1);
