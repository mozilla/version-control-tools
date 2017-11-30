#!/usr/bin/env python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# This script provides data validation around the bloxtool CLI, which
# retrieves Mozilla IP address ranges froma third party vendor. The
# script runs as a recurring systemd task.

import ipaddress
import json
import subprocess
import sys
from pathlib import Path

from voluptuous import Schema, Invalid as VoluptuousInvalid, truth
from voluptuous.humanize import validate_with_humanized_errors


@truth
def is_ip_address_network(value):
    try:
        # This call will raise a ValueError if value is not a valid ip address range
        ipaddress.ip_network(value, strict=True)
        return True

    except ValueError:
        return False


IP_RANGES_FILE = Path('/var/hg/moz-ip-ranges.txt')
BLOXTOOL_CONFIG_FILE = Path('/etc/mercurial/bloxtool.ini')
COMMAND = [
    '/var/hg/venv_tools/bin/bloxtool',
    'network',
    'search',
    'attribute',
    'subnet-purpose',
    'value',
    'nat-pool',
    '--format=json',
    f'--config={BLOXTOOL_CONFIG_FILE}',
]

JSON_SCHEMA = Schema([
        {
            'comment': str,
            '_ref': str,
            'network': is_ip_address_network,
            'network_view': str,
        }
    ], extra=False, required=True)


if __name__ == '__main__':
    try:
        # Get raw string output and convert to Python dict
        process_output = subprocess.run(COMMAND, check=True, encoding='utf-8', stdout=subprocess.PIPE).stdout
        output_as_dict = json.loads(process_output)

        # Verify dict schema
        validate_with_humanized_errors(output_as_dict, JSON_SCHEMA)

        # Write data to a temp file, atomically rewrite the the IP ranges file
        temp_file_path = IP_RANGES_FILE.with_suffix('.tmp')
        with temp_file_path.open(mode='w') as temp_file:
            ip_ranges = (i['network'] for i in output_as_dict)
            temp_file.writelines(ip_ranges)

        temp_file_path.rename(IP_RANGES_FILE)

    except subprocess.CalledProcessError as cpe:
        sys.exit('An error occurred while executing the bloxtool command.')

    except json.JSONDecodeError as jde:
        sys.exit('An error occurred parsing the bloxtool output as JSON.')

    except VoluptuousInvalid as vi:
        sys.exit('The JSON data from bloxtool does not match the required schema.')
