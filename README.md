# Mozilla Version Control Tools

This repository contains tools, extensions, hooks, etc to support version
control at Mozilla.

Most documentation exists in the ``docs/`` directory. It can be
[viewed online](https://mozilla-version-control-tools.readthedocs.io/en/latest/)
on Read the Docs.

## Contributing

- All contributors must abide by the Mozilla Code of Conduct.

- The canonical Mercurial repository is https://hg.mozilla.org/hgcustom/version-control-tools/.
  The GitHub copy at https://github.com/mozilla/version-control-tools is a mirror and is
  not used for development.

- Patches are taken through [Mozilla Phabricator](https://phabricator.services.mozilla.com/).
  For new contributors wanting to quickly submit changes, [`moz-phab`](https://github.com/mozilla-conduit/review) is recommended.

- Bugs are tracked [on Bugzilla](https://bugzilla.mozilla.org), under the components prefixed by `Developer Services :: Mercurial:`.

- If you are interested in getting in touch with the people who maintain
  this repository, join the ``vcs`` channel on ``chat.mozilla.org``.

## Testing

To create a test environment and run tests, you should use the `./run` script
at the root of the repository. This script wraps common `docker-compose`
commands to provide better ergonomics and good testing defaults.

The test runner and all it's dependencies are contained in a Docker image.
The state of your version-control-tools checkout is mounted into the container
built from that image and tests are run inside the container using the source
on your host's filesystem. To do this, a `.env` file must be created to tell
the container about which user on the host system is running the tests.

You can run the following command to create a `.env` file:

```shell
  ./run env > .env
```

Now you can run the tests via:

```shell
  ./run tests path/to/test --with-hg=5.3.2
```

### Ansible-to-Docker Cluster

The configuration of the production server is managed by the Ansible configs
in `ansible/`. To test these configs and much of the code that depends on them,
we have a custom Docker image build process which applies the Ansible roles to
Docker images and creates a mock cluster of Docker containers that is mostly
identical to the production hosts of `hg.mozilla.org`.

Running these tests is slow and uses a lot of CPU resources. It is recommended
to use `-j` to limit the number of concurrently running tests. If you don't
want to run the Ansible-to-Docker cluster tests, you can use the `--no-docker`
flag when running the tests.

