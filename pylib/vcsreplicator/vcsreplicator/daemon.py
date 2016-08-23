# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import, unicode_literals

import signal
import sys


def run_in_loop(logger, fn, onetime=False, **kwargs):
    """Run a function multiple times.

    The function ``fn`` will be called  in an infinite loop until the process
    receives a SIGINT or SIGTERM or unless ``onetime`` is set, in which case
    ``fn`` will be called once.

    ``fn`` receives ``**kwargs`` as arguments. It also receives an ``alive``
    named argument which is a list of a single bool that indicates whether the
    process should still be alive. ``fn`` functions can use this to implement
    their own looping or long-running logic that terminates gracefully if this
    function's signal handlers receive a signal to terminate.
    """
    signal_count = [0]
    alive = [True]

    def signal_exit(signum, frame):
        logger.warn('received signal %d' % signum)
        signal_count[0] += 1
        alive[0] = False

        if signal_count[0] == 1:
            logger.warn('exiting gracefully')
            return

        # If this is a subsequent signal, convert to forceful exit.
        logger.warn('already received exit signal; forcefully aborting')
        sys.exit(1)

    oldint = signal.signal(signal.SIGINT, signal_exit)
    oldterm = signal.signal(signal.SIGTERM, signal_exit)
    try:
        while alive[0]:
            try:
                fn(alive=alive, **kwargs)
            except Exception:
                logger.exception('exception in daemon loop function')
                logger.warn('executing loop exiting after error')
                return 1

            if onetime:
                break

        logger.warn('executing loop exiting gracefully')
        return 0
    finally:
        signal.signal(signal.SIGINT, oldint)
        signal.signal(signal.SIGTERM, oldterm)
