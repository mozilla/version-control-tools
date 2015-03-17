# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# This script is used to manage Docker containers in the context of running
# Mercurial tests.

from __future__ import absolute_import

import base64
import docker
import json
import os
import pickle
import requests
import ssl
import subprocess
import sys
import tarfile
import urlparse
import uuid
import warnings
from contextlib import contextmanager
from io import BytesIO

import concurrent.futures as futures
from coverage.data import CoverageData

from .util import (
    wait_for_amqp,
    wait_for_http,
)


HERE = os.path.abspath(os.path.dirname(__file__))
DOCKER_DIR = os.path.normpath(os.path.join(HERE, '..', 'docker'))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))


def params_from_env(env):
    """Obtain Docker connect parameters from the environment.

    This returns a tuple that should be used for base_url and tls arguments
    of Docker.__init__.
    """
    host = env.get('DOCKER_HOST', None)
    tls = False

    if env.get('DOCKER_TLS_VERIFY'):
        tls = True

    # This is likely encountered with boot2docker.
    cert_path = env.get('DOCKER_CERT_PATH')
    if cert_path:
        ca_path = os.path.join(cert_path, 'ca.pem')
        tls_cert_path = os.path.join(cert_path, 'cert.pem')
        tls_key_path = os.path.join(cert_path, 'key.pem')

        # Hostnames will attempt to be verified by default. We don't know what
        # the hostname should be, so don't attempt it.
        tls = docker.tls.TLSConfig(client_cert=(tls_cert_path, tls_key_path),
                ssl_version=ssl.PROTOCOL_TLSv1, ca_cert=ca_path, verify=True,
                assert_hostname=False)

    # docker-py expects the protocol to have something TLS in it. tcp:// won't
    # work. Hack around it until docker-py works as expected.
    if tls and host:
        if host.startswith('tcp://'):
            host = host.replace('tcp://', 'https://')

    return host, tls


class Docker(object):
    def __init__(self, state_path, url, tls=False):
        self._ddir = DOCKER_DIR
        self._state_path = state_path
        self.state = {
            'images': {},
            'containers': {},
            'last-bmodb-id': None,
            'last-bmoweb-id': None,
            'last-pulse-id': None,
            'last-rbweb-id': None,
            'last-bmodb-bootstrap-id': None,
            'last-bmoweb-bootstrap-id': None,
            'last-rbweb-bootstrap-id': None,
            'last-autolanddb-id': None,
            'last-autoland-id': None,
            'last-hgmaster-id': None,
            'last-hgweb-id': None,
            'last-ldap-id': None,
        }

        if os.path.exists(state_path):
            with open(state_path, 'rb') as fh:
                self.state = json.load(fh)

        keys = (
            'last-bmodb-id',
            'last-bmoweb-id',
            'last-pulse-id',
            'last-rbweb-id',
            'last-bmodb-bootstrap-id',
            'last-bmoweb-bootstrap-id',
            'last-rbweb-bootstrap-id',
            'last-autolanddb-id',
            'last-autoland-id',
            'last-hgmaster-id',
            'last-hgweb-id',
            'last-ldap-id',
        )
        for k in keys:
            self.state.setdefault(k, None)

        self.client = docker.Client(base_url=url, tls=tls)

        # Try to obtain a network hostname for the Docker server. We use this
        # for determining where to look for opened ports.
        # This is a bit complicated because Docker can be running from a local
        # socket or or another host via something like boot2docker.
        # TODO look at network info for Docker and extract IP address instead.
        docker_url = urlparse.urlparse(self.client.base_url)
        self.docker_hostname = docker_url.hostname
        if 'unix' in docker_url.scheme:
            self.docker_hostname = 'localhost'

    def is_alive(self):
        """Whether the connection to Docker is alive."""
        # This is a layering violation with docker.client, but meh.
        try:
            self.client._get(self.client._url('/version'), timeout=1)
            return True

        # docker-py, urllib3, and Python's ssl packages all seem to have
        # a difficult time talking to boot2docker under Python 2.7.9. We
        # report a warning in this case and recommend using Python 2.7.8
        # until a workaround is known.
        except requests.exceptions.SSLError as e:
            if 'CERTIFICATE_VERIFY_FAILED' not in str(e.message):
                return False

            if sys.version_info[0:3] != (2, 7, 9):
                return False

            warnings.warn(
                'SSL error encountered talking to Docker. This is a known '
                'issue with Python 2.7.9, which you are running. It is '
                'recommended to use Python 2.7.8 until a workaround is '
                'identified: %s' % e.message)

            return False

        except requests.exceptions.RequestException as e:
            return False

    def ensure_built(self, name, verbose=False, nocache=False):
        """Ensure a Docker image from a builder directory is built and up to date.

        This function is docker build++. Under the hood, it talks to the same
        ``build`` Docker API. However, it does one important thing differently:
        it builds the context archive manually.

        We supplement all contexts with the content of the source in this
        repository related to building Docker containers. This is done by
        scanning the Dockerfile for references to extra files to include.

        If a line in the Dockerfile has the form ``# %include <path>``,
        the relative path specified on that line will be matched against
        files in the source repository and added to the context under the
        path ``extra/vct/``. If an entry ends in a ``/``, we add all files
        under that directory. Otherwise, we assume it is a literal match and
        only add a single file.

        This added content can be ``ADD``ed to the produced image inside the
        Dockerfile. If the content changes, the Docker image ID changes and the
        cache is invalidated. This effectively allows downstream consumers to
        call ``ensure_built()`` as there *is the image up to date* check.
        """

        p = os.path.join(self._ddir, 'builder-%s' % name)
        if not os.path.isdir(p):
            raise Exception('Unknown Docker builder name: %s' % name)

        vct_paths = []
        with open(os.path.join(p, 'Dockerfile'), 'rb') as fh:
            for line in fh:
                line = line.rstrip()
                if not line.startswith('# %include'):
                    continue

                vct_paths.append(line[len('# %include '):])

        # We build the build context for the image manually because we need to
        # include things outside of the directory containing the Dockerfile.
        buf = BytesIO()
        tar = tarfile.open(mode='w', fileobj=buf)

        for root, dirs, files in os.walk(p):
            for f in files:
                if f == '.dockerignore':
                    raise Exception('.dockerignore not currently supported!')

                full = os.path.join(root, f)
                rel = full[len(p)+1:]
                tar.add(full, arcname=rel)

        # Include extra context from us and other support tools used for
        # creating [bootstrapped] images so Dockerfiles can ADD these files and
        # force cache invalidation of produced images if our logic changes.

        # Add ourself.
        tar.add(os.path.join(HERE, 'docker.py'), 'extra/vcttesting/docker.py')

        # Add the script for managing docker. This shouldn't be needed, but you
        # never know.
        tar.add(os.path.join(HERE, '..', 'docker-control.py'),
                'extra/docker-control.py')

        if vct_paths:
            # We grab the set of tracked files in this repository.
            hg = os.path.join(ROOT, 'venv', 'bin', 'hg')
            env = dict(os.environ)
            env['HGRCPATH'] = '/dev/null'
            args = [hg, '-R', ROOT, 'locate']
            null = open(os.devnull, 'wb')
            output = subprocess.check_output(args, env=env, cwd='/',
                                             stderr=null)

            vct_files = output.splitlines()
            added = set()
            for p in vct_paths:
                ap = os.path.join(ROOT, p)
                if not os.path.exists(ap):
                    raise Exception('specified path not under version '
                                    'control: %s' % p)
                if p.endswith('/'):
                    for f in vct_files:
                        if not f.startswith(p) and p != '/':
                            continue
                        full = os.path.join(ROOT, f)
                        rel = 'extra/vct/%s' % f
                        if full in added:
                            continue
                        tar.add(full, rel)
                else:
                    full = os.path.join(ROOT, p)
                    if full in added:
                        continue
                    rel = 'extra/vct/%s' % p
                    tar.add(full, rel)

        tar.close()

        # Need to seek to beginning so .read() inside docker.client will return
        # data.
        buf.seek(0)

        # The API here is wonky, possibly due to buggy behavior in
        # docker.client always setting stream=True if version > 1.8.
        # We assume this is a bug that will change behavior later and work
        # around it by ensuring consistent behavior.
        for stream in self.client.build(fileobj=buf, custom_context=True,
                                        rm=True, stream=True, nocache=nocache):
            s = json.loads(stream)
            if 'stream' not in s:
                continue

            s = s['stream']
            if verbose:
                # s has newlines, so don't go through print().
                sys.stdout.write('%s> %s' % (name, s))
            if s.startswith('Successfully built '):
                image = s[len('Successfully built '):]
                # There is likely a trailing newline.
                full_image = self.get_full_image(image.rstrip())

                # We only tag the image once to avoid redundancy.
                have_tag = False
                for i in self.client.images():
                    if i['Id'] == full_image:
                        for repotag in i['RepoTags']:
                            repo, tag = repotag.split(':')
                            if repo == name:
                                have_tag = True

                        break
                if not have_tag:
                    self.client.tag(full_image, name, str(uuid.uuid1()))

                return full_image

        raise Exception('Unable to confirm image was built')

    def ensure_images_built(self, names, existing=None, verbose=False):
        """Ensure that multiple images are built.

        ``names`` is a list of Docker images to build.
        """
        existing = existing or {}
        images = dict(existing)
        missing = set(names) - set(existing.keys())

        def build(name, **kwargs):
            image = self.ensure_built(name, **kwargs)
            return name, image

        with futures.ThreadPoolExecutor(len(missing)) as e:
            fs = [e.submit(build, name, verbose=verbose) for name in missing]

            for f in futures.as_completed(fs):
                name, image = f.result()
                images[name] = image

        return images

    def build_hgmo(self, images=None, verbose=False):
        """Ensure the images for a hg.mozilla.org service are built.

        hg-master runs the ssh service while hg-slave runs hgweb. The mirroring
        and other bits should be the same as in production with the caveat that
        LDAP integration is probably out of scope.
        """
        images = self.ensure_images_built(['hgmaster', 'hgweb', 'ldap'],
                                          existing=images, verbose=verbose)

        self.state['last-hgmaster-id'] = images['hgmaster']
        self.state['last-hgweb-id'] = images['hgweb']
        self.state['last-ldap-id'] = images['ldap']

        return images

    def build_mozreview(self, images=None, verbose=False):
        """Ensure the images for a MozReview service are built.

        bmoweb's entrypoint does a lot of setup on first run. This takes many
        seconds to perform and this cost is unacceptable for efficient test
        running. So, when we build the BMO images, we create throwaway
        containers and commit the results to a new image. This allows us to
        spin up multiple bmoweb containers very quickly.
        """
        state_images = self.state['images']

        images = self.ensure_images_built([
            'autolanddb',
            'autoland',
            'bmodb-volatile',
            'bmoweb',
            'ldap',
            'pulse',
            #'rbweb',
        ], existing=images, verbose=verbose)

        self.state['last-autolanddb-id'] = images['autolanddb']
        self.state['last-autoland-id'] = images['autoland']
        self.state['last-bmodb-id'] = images['bmodb-volatile']
        self.state['last-bmoweb-id'] = images['bmoweb']
        self.state['last-ldap-id'] = images['ldap']
        self.state['last-pulse-id'] = images['pulse']
        #self.state['last-rbweb-id'] = images['rbweb']

        # The keys for the bootstrapped images are derived from the base
        # images they depend on. This means that if we regenerate a new
        # base image, the bootstrapped images will be regenerated.
        bmodb_bootstrapped_key = 'bmodb-bootstrapped:%s' % images['bmodb-volatile']
        bmoweb_bootstrapped_key = 'bmoweb-bootstrapped:%s:%s' % (
                images['bmodb-volatile'], images['bmoweb'])
        autolanddb_bootstrapped_key = 'autolanddb-bootstrapped:%s' % images['autolanddb']
        autoland_bootstrapped_key = 'autoland-bootstrapped:%s' % images['autoland']
        #rbweb_bootstrapped_key = 'rbweb-bootstrapped:%s:%s' % (db_image,
        #        images['rbweb'])

        have_bmodb = bmodb_bootstrapped_key in state_images
        have_bmoweb = bmoweb_bootstrapped_key in state_images
        have_ldap = 'ldap' in state_images
        have_pulse = 'pulse' in state_images
        have_autolanddb = autolanddb_bootstrapped_key in state_images
        have_autoland = autoland_bootstrapped_key in state_images
        #have_rbweb = rbweb_bootstrapped_key in state_images

        if (have_bmodb and have_bmoweb and have_ldap and have_pulse and
                have_autolanddb and have_autoland): # and have_rbweb:
            return {
                'autolanddb': state_images[autolanddb_bootstrapped_key],
                'autoland': state_images[autoland_bootstrapped_key],
                'bmodb': state_images[bmodb_bootstrapped_key],
                'bmoweb': state_images[bmoweb_bootstrapped_key],
                'ldap': state_images['ldap'],
                'pulse': state_images['pulse'],
                #'rbweb': state_images[rbweb_bootstrapped_key],
            }

        bmodb_id = self.client.create_container(images['bmodb-volatile'],
                environment={'MYSQL_ROOT_PASSWORD': 'password'})['Id']

        bmoweb_environ = {}

        if 'FETCH_BMO' in os.environ:
            bmoweb_environ['FETCH_BMO'] = '1'

        bmoweb_id = self.client.create_container(images['bmoweb'],
                                                 environment=bmoweb_environ)['Id']

        autolanddb_id = self.client.create_container(images['autolanddb'])['Id']
        autoland_id = self.client.create_container(images['autoland'])['Id']

        #rbweb_id = self.client.create_container(images['rbweb'])['Id']

        with self._start_container(bmodb_id) as db_state:
            web_params = {
                'links': [(db_state['Name'], 'bmodb')],
                'port_bindings': {80: None},
            }
            rbweb_params = {
                'links': [(db_state['Name'], 'rbdb')],
                'port_bindings': {80: None},
            }
            with self._start_container(bmoweb_id, **web_params) as web_state:
                #with self._start_container(rbweb_id, **rbweb_params) as rbweb_state:
                bmoweb_port = int(web_state['NetworkSettings']['Ports']['80/tcp'][0]['HostPort'])
                #rbweb_port = int(rbweb_state['NetworkSettings']['Ports']['80/tcp'][0]['HostPort'])
                print('waiting for containers to bootstrap')
                wait_for_http(self.docker_hostname, bmoweb_port, path='xmlrpc.cgi')
                #wait_for_http(self.docker_hostname, rbweb_port)

        bmodb_unique_id = str(uuid.uuid1())
        bmoweb_unique_id = str(uuid.uuid1())
        autolanddb_unique_id = str(uuid.uuid1())
        autoland_unique_id = str(uuid.uuid1())
        #rbweb_unique_id = str(uuid.uuid1())

        print('committing bootstrapped images')

        # Save an image of the stopped containers.
        # We tag with a unique ID so we can identify all bootrapped images
        # easily from Docker's own metadata. We have to give a tag becaue
        # Docker will forget the repository name if a name image has only a
        # repository name as well.
        with futures.ThreadPoolExecutor(4) as e:
            bmodb_future = e.submit(self.client.commit, bmodb_id,
                                    repository='bmodb-volatile-bootstrapped',
                                    tag=bmodb_unique_id)
            bmoweb_future = e.submit(self.client.commit, bmoweb_id,
                                     repository='bmoweb-bootstrapped',
                                     tag=bmoweb_unique_id)
            autolanddb_future = e.submit(self.client.commit, autolanddb_id,
                                         repository='autolanddb-bootstrapped',
                                         tag=autolanddb_unique_id)
            autoland_future = e.submit(self.client.commit, autoland_id,
                    repository='autoland-bootstrapped',
                    tag=autoland_unique_id)
            #rbweb_future = e.submit(self.client.commit, rbweb_id,
            #        repository='rbweb-bootstrapped',
            #        tag=rbweb_unique_id)

        bmodb_bootstrap = bmodb_future.result()['Id']
        bmoweb_bootstrap = bmoweb_future.result()['Id']
        autolanddb_bootstrap = autolanddb_future.result()['Id']
        autoland_bootstrap = autoland_future.result()['Id']
        #rbweb_bootstrap = rbweb_future.result()['Id']
        state_images[bmodb_bootstrapped_key] = bmodb_bootstrap
        state_images[bmoweb_bootstrapped_key] = bmoweb_bootstrap
        state_images['ldap'] = images['ldap']
        state_images['pulse'] = images['pulse']
        state_images[autolanddb_bootstrapped_key] = autolanddb_bootstrap
        state_images[autoland_bootstrapped_key] = autoland_bootstrap
        #state_images[rbweb_bootstrapped_key] = rbweb_bootstrap
        self.state['last-bmodb-bootstrap-id'] = bmodb_bootstrap
        self.state['last-bmoweb-bootstrap-id'] = bmoweb_bootstrap
        self.state['last-autolanddb-bootstrap-id'] = autolanddb_bootstrap
        self.state['last-autoland-bootstrap-id'] = autoland_bootstrap
        #self.state['last-rbweb-bootstrap-id'] = rbweb_bootstrap
        self.save_state()

        print('removing non-bootstrapped containers')

        with futures.ThreadPoolExecutor(2) as e:
            e.submit(self.client.remove_container, bmoweb_id)
            e.submit(self.client.remove_container, bmodb_id)
            #e.submit(self.client.remove_container, rbweb_id)

        print('bootstrapped images created')

        return {
            'autolanddb': autolanddb_bootstrap,
            'autoland': autoland_bootstrap,
            'bmodb': bmodb_bootstrap,
            'bmoweb': bmoweb_bootstrap,
            'ldap': images['ldap'],
            'pulse': images['pulse'],
            #'rbweb': rbweb_bootstrap,
        }

    def start_mozreview(self, cluster, hostname=None, http_port=80,
            ldap_image=None, ldap_port=None, pulse_port=None,
            rbweb_port=None, db_image=None, web_image=None, pulse_image=None,
            rbweb_image=None, autolanddb_image=None,
            autoland_image=None, autoland_port=None, verbose=False):

        start_ldap = False
        if ldap_port:
            start_ldap = True

        start_pulse = False
        if pulse_port:
            start_pulse = True

        start_autoland = False
        if autoland_port:
            start_autoland = True

        if (not db_image or not web_image or not ldap_image
                or not pulse_image or not autolanddb_image
                or not autoland_image):
            images = self.build_mozreview(verbose=verbose)
            autolanddb_image = images['autolanddb']
            autoland_image = images['autoland']
            db_image = images['bmodb']
            ldap_image = images['ldap']
            web_image = images['bmoweb']
            pulse_image = images['pulse']

        containers = self.state['containers'].setdefault(cluster, [])

        if not hostname:
            hostname = self.docker_hostname
        url = 'http://%s:%s/' % (hostname, http_port)

        with futures.ThreadPoolExecutor(5) as e:
            # Create containers concurrently - no race conditions here.
            f_db_create = e.submit(self.client.create_container, db_image,
                    environment={'MYSQL_ROOT_PASSWORD': 'password'})
            if start_pulse:
                f_pulse_create = e.submit(self.client.create_container,
                        pulse_image)

            f_web_create = e.submit(self.client.create_container,
                    web_image, environment={'BMO_URL': url})

            if start_ldap:
                f_ldap_create = e.submit(self.client.create_container,
                                         ldap_image)

            if start_autoland:
                f_autolanddb_create = e.submit(self.client.create_container,
                        autolanddb_image)

                f_autoland_create = e.submit(self.client.create_container,
                        autoland_image)

            #f_rbweb_create = e.submit(self.client.create_container,
            #        rbweb_image)


            # We expose the database to containers. Start it first.
            db_id = f_db_create.result()['Id']
            containers.append(db_id)
            f_db_start = e.submit(self.client.start, db_id)

            if start_autoland:
                autolanddb_id = f_autolanddb_create.result()['Id']
                containers.append(autolanddb_id)
                f_start_autolanddb = e.submit(self.client.start, autolanddb_id)

            # RabbitMQ takes a while to start up. Start it before other
            # containers. (We probably could have a callback-driven mechanism
            # here to ensure no time is lost. But that is more complex.)
            if start_pulse:
                pulse_id = f_pulse_create.result()['Id']
                containers.append(pulse_id)
                f_start_pulse = e.submit(self.client.start, pulse_id,
                                         port_bindings={5672: pulse_port})


            if start_ldap:
                ldap_id = f_ldap_create.result()['Id']
                containers.append(ldap_id)
                f_start_ldap = e.submit(self.client.start, ldap_id,
                                        port_bindings={389: ldap_port})

            f_db_start.result()
            db_state = self.client.inspect_container(db_id)

            web_id = f_web_create.result()['Id']
            containers.append(web_id)

            if start_autoland:
                f_start_autolanddb.result()
                autolanddb_state = self.client.inspect_container(autolanddb_id)
                autoland_id = f_autoland_create.result()['Id']
                containers.append(autoland_id)
                autoland_state = self.client.inspect_container(autoland_id)

            #rbweb_id = f_rbweb_create.result()['Id']
            #containers.append(rbweb_id)

            # At this point, all containers have started.
            self.save_state()

            f_start_web = e.submit(self.client.start, web_id,
                    links=[(db_state['Name'], 'bmodb')],
                    port_bindings={80: http_port})
            f_start_web.result()
            web_state = self.client.inspect_container(web_id)

            #f_start_rbweb = e.submit(self.client.start, rbweb_id,
            #        links=[
            #            (db_state['Name'], 'rbdb'),
            #            (web_state['Name'], 'bzweb'),
            #        ],
            #        port_bindings={80: rbweb_port})
            #f_start_rbweb.result()
            #rbweb_state = self.client.inspect_container(rbweb_id)

            if start_autoland:
                bind_path = os.path.abspath(os.path.dirname(self._state_path))
                f_start_autoland = e.submit(self.client.start, autoland_id,
                        links=[(autolanddb_state['Name'], 'db')],
                        port_bindings={80: autoland_port})
                f_start_autoland.result()
                autoland_state = self.client.inspect_container(autoland_id)

            if start_pulse:
                f_start_pulse.result()
                pulse_state = self.client.inspect_container(pulse_id)

            if start_ldap:
                f_start_ldap.result()
                ldap_state = self.client.inspect_container(ldap_id)

        wait_bmoweb_port = web_state['NetworkSettings']['Ports']['80/tcp'][0]['HostPort']
        if start_pulse:
            wait_rabbit_port = pulse_state['NetworkSettings']['Ports']['5672/tcp'][0]['HostPort']
        #wait_rbweb_port = rbweb_state['NetworkSettings']['Ports']['80/tcp'][0]['HostPort']

        #rb_url = 'http://%s:%s/' % (hostname, wait_rbweb_port)

        print('waiting for Bugzilla to start')
        wait_for_http(self.docker_hostname, wait_bmoweb_port)
        #wait_for_http(self.docker_hostname, wait_rbweb_port)
        if start_pulse:
            wait_for_amqp(self.docker_hostname, wait_rabbit_port, 'guest', 'guest')
        print('Bugzilla accessible on %s' % url)
        #print('Review Board accessible at %s' % rb_url)

        result = {
            'bugzilla_url': url,
            'db_id': db_id,
            'web_id': web_id,
            'pulse_host': self.docker_hostname,
            'pulse_port': pulse_port,
        }

        if start_autoland:
            result['autolanddb_id'] = autolanddb_id
            result['autoland_id'] = autoland_id

        if start_ldap:
            ldap_port = int(ldap_state['NetworkSettings']['Ports']['389/tcp'][0]['HostPort'])
            result['ldap_id'] = ldap_id
            result['ldap_uri'] = 'ldap://%s:%d/' % (self.docker_hostname,
                                                    ldap_port)

        return result

    def stop_bmo(self, cluster):
        count = 0

        with futures.ThreadPoolExecutor(4) as e:
            for container in reversed(self.state['containers'].get(cluster, [])):
                count += 1
                e.submit(self.client.remove_container, container, force=True)

        print('stopped %d containers' % count)

        try:
            del self.state['containers'][cluster]
            self.save_state()
        except KeyError:
            pass

    def build_all_images(self, verbose=False):
        images = self.ensure_images_built([
            'autolanddb',
            'autoland',
            'bmodb-volatile',
            'bmoweb',
            'hgmaster',
            'hgweb',
            'ldap',
            'pulse',
            #'rbweb',
        ], verbose=verbose)

        with futures.ThreadPoolExecutor(2) as e:
            f_mr = e.submit(self.build_mozreview, images=images,
                            verbose=verbose)
            f_hgmo = e.submit(self.build_hgmo, images=images, verbose=verbose)

        return f_mr.result(), f_hgmo.result()

    def _get_files_from_http_container(self, builder, message):
        image = self.ensure_built(builder, verbose=True)
        container = self.client.create_container(image)['Id']

        with self._start_container(container, port_bindings={80: None}) as state:
            port = int(state['NetworkSettings']['Ports']['80/tcp'][0]['HostPort'])

            print(message)
            wait_for_http(self.docker_hostname, port, timeout=120)

            res = requests.get('http://%s:%s/' % (self.docker_hostname, port))

            files = {}
            for filename, data in res.json().items():
                files[filename] = base64.b64decode(data)

        self.client.remove_container(container)

        return files

    def build_reviewboard_eggs(self):
        return self._get_files_from_http_container('eggbuild',
            'Generating eggs...')

    def build_mercurial_rpms(self):
        return self._get_files_from_http_container('hgrpm',
            'Generating RPMs...')

    def get_full_image(self, image):
        for i in self.client.images():
            if i['Id'][0:12] == image:
                return i['Id']

        return image

    def prune_images(self):
        """Prune images that are old and likely unused."""
        running = set(self.get_full_image(c['Image'])
                      for c in self.client.containers())

        candidates = []

        ignore_images = set([
            self.state['last-bmodb-id'],
            self.state['last-bmoweb-id'],
            self.state['last-pulse-id'],
            self.state['last-rbweb-id'],
            self.state['last-db-bootstrap-id'],
            self.state['last-web-bootstrap-id'],
            self.state['last-rbweb-bootstrap-id'],
            self.state['last-autolanddb-bootstrap-id'],
            self.state['last-autoland-bootstrap-id'],
            self.state['last-hgmaster-id'],
            self.state['last-hgweb-id'],
            self.state['last-ldap-id'],
        ])

        relevant_repos = set([
            'bmoweb',
            'bmoweb-bootstrapped',
            'bmodb-volatile',
            'bmodb-volatile-bootstrapped',
            'pulse',
            'rbweb',
            'rbweb-bootstrapped',
            'autolanddb',
            'autolanddb-bootstrapped',
            'autoland',
            'autoland-bootstrapped',
            'hgmaster',
            'hgweb',
            'ldap',
        ])

        for i in self.client.images():
            iid = i['Id']

            # Don't do anything with images attached to running containers -
            # Docker won't allow it.
            if iid in running:
                continue

            # Don't do anything with our last used images.
            if iid in ignore_images:
                continue

            for repotag in i['RepoTags']:
                repo, tag = repotag.split(':')
                if repo in relevant_repos:
                    candidates.append(iid)
                    break

        retained = {}
        for key, image in sorted(self.state['images'].items()):
            if image in candidates:
                retained[key] = image

        with futures.ThreadPoolExecutor(4) as e:
            for iid in candidates:
                print('Removing image %s' % iid)
                e.submit(self.client.remove_image, iid)

        self.state['images'] = retained
        self.save_state()

    def save_state(self):
        with open(self._state_path, 'wb') as fh:
            json.dump(self.state, fh)

    @contextmanager
    def _start_container(self, cid, **kwargs):
        """Context manager for starting and stopping a Docker container.

        The container with id ``cid`` will be started when the context manager is
        entered and stopped when the context manager is execited.

        The context manager receives the inspected state of the container,
        immediately after it is started.
        """
        self.client.start(cid, **kwargs)
        try:
            state = self.client.inspect_container(cid)
            yield state
        finally:
            self.client.stop(cid, timeout=20)

    def get_file_content(self, cid, path):
        """Get the contents of a file from a container."""
        r = self.client.copy(cid, path)
        buf = BytesIO(r.read())
        buf.seek(0)
        t = tarfile.open(mode='r', fileobj=buf)
        fp = t.extractfile(os.path.basename(path))
        return fp.read()

    def get_directory_contents(self, cid, path, tar='/bin/tar'):
        """Obtain the contents of all files in a directory in a container.

        This is done by invoking "tar" inside the container and piping the
        results to us.

        This returns an iterable of ``tarfile.TarInfo``, fileobj 2-tuples.
        """
        data = self.client.execute(cid, [tar, '-c', '-C', path, '-f', '-', '.'],
                                   stderr=False)
        buf = BytesIO(data)
        t = tarfile.open(mode='r', fileobj=buf)
        for member in t:
            f = t.extractfile(member)
            member.name = member.name[2:]
            yield member, f

    def get_code_coverage(self, cid, filemap=None):
        """Obtain code coverage data from a container.

        Containers can be programmed to collect code coverage from executed
        programs automatically. Our convention is to place coverage files in
        ``/coverage``.

        This method will fetch coverage files and parse them into data
        structures, which it will emit.

        If a ``filemap`` dict is passed, it will be used to map filenames
        inside the container to local filesystem paths. When present,
        files not inside the map will be ignored.
        """
        filemap = filemap or {}

        for member, fh in self.get_directory_contents(cid, '/coverage'):
            if not member.name.startswith('coverage.'):
                continue

            data = pickle.load(fh)

            c = CoverageData(basename=member.name,
                             collector=data.get('collector'))

            lines = {}
            for f, linenos in data.get('lines', {}).items():
                newname = filemap.get(f)
                if not newname:
                    # Ignore entries missing from map.
                    if filemap:
                        continue

                    newname = f

                lines[newname] = dict.fromkeys(linenos, None)

            arcs = {}
            for f, arcpairs in data.get('arcs', {}).items():
                newname = filemap.get(f)
                if not newname:
                    if filemap:
                        continue

                    newname = f

                arcs[newname] = dict.fromkeys(arcpairs, None)

            if not lines and not arcs:
                continue

            c.lines = lines
            c.arcs = arcs

            yield c
