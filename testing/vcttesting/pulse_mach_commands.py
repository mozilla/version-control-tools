# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os

from mach.decorators import (
    CommandArgument,
    CommandProvider,
    Command,
)

@CommandProvider
class PulseCommands(object):
    def _get_consumer(self, class_name):
        import mozillapulse.consumers as consumers

        cls = getattr(consumers, class_name)
        pulse_host = None
        pulse_port = None

        if 'PULSE_HOST' in os.environ:
            pulse_host = os.environ['PULSE_HOST']
        if 'PULSE_PORT' in os.environ:
            pulse_port = int(os.environ['PULSE_PORT'])

        if not pulse_host:
            raise Exception('Can not find Pulse host. Try setting PULSE_HOST')
        if not pulse_port:
            raise Exception('Can not find Pulse port. Try setting PULSE_PORT')

        return cls(user='guest', password='guest', host=pulse_host,
                port=pulse_port, topic='#', ssl=False)

    @Command('create-exchange', category='pulse',
        description='Create an exchange')
    @CommandArgument('classname',
        help='Pulse class name of exchange to initialize')
    def create_exchange(self, classname):
        from kombu import Exchange
        c = self._get_consumer(classname)

        exchange = Exchange(c.exchange, type='topic')
        exchange(c.connection).declare()
