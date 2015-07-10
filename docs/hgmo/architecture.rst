.. _hgmo_architecture:

============
Architecture
============

hg.mozilla.org consists of multiple servers and network appliances. To
understand how they all interact, it helps to understand the services
that are exposed.

Communication with hg.mozilla.org likely occurs over one of the following
ports:

* 22/tcp (SSH)
* 80/tcp (HTTP)
* 443/tcp (HTTPS)

Interaction with these ports occurs through a load balancer in a
Mozilla data center in Santa Clara, Calfifornia.

Connections to ports 80 and 443 are routed to a pool of read-only
mirrors. We call this the *hgweb* pool. Connections to port 22 are
routed to a single *master* server. We call this the *hgssh* server.
There is a warm standby for the *hgssh* server that is made active
should the primary server fail.

All writes (pushes) are performed via SSH and are thus handled by the
master server.

The SSH server authenticates clients via SSH public key authentication
by consulting Mozilla's LDAP server. Account info including SSH public
keys and access bits are stored in LDAP.

Authenticated SSH sessions invoke the ``pash.py`` script from the
version-control-tools repository. This script performs additional
checking before eventually spawning an ``hg serve`` process, which
communicates with the Mercurial client to interact with the requested
repository.

Various hooks and extensions on the Mercurial server intercept change
events and trigger replication of changes. Replication is currently
very crude, but effective: the master server establishes an SSH
connection to each mirror and executes a script telling the mirror to
pull changes from a specific repository. Each mirror has its own
local disk holding repository data. There is no global transaction,
so there is a window during each push where the mirrors expose
inconsistent data. In practice, it is rare for a client to be
impacted by this temporary inconsistency.

The master SSH server holds its repository data on an NFS volume,
which is backed by an expensive network appliance. If the master SSH
server goes down, the warm standby has immediate access to repository
data.
