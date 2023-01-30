# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import print_function

import shlex
import subprocess
import sys


def run_command(command_string):
    fixed_command_string = command_string.lstrip().rstrip()

    # Sent output to `/dev/null`.
    subcommand = subprocess.Popen(
        shlex.split(fixed_command_string),
        stdin=None,
        stderr=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
    )

    while True:
        l = subcommand.stdout.readline()
        if not l:
            break

    out_fd.close()


def prompt_user(prompt_string, options, period=True):
    print("")
    print("0) Exit.")

    for index, option in enumerate(options, start=1):
        option_display = f"{index}) {option}"
        if period:
            option_display += "."
        print(option_display)

    print("")

    selection = input(f"{prompt_string} ")

    if not selection.isdigit():
        sys.stderr.write("Please select the number corresponding to the option\n")
        return prompt_user(prompt_string, options)

    selection = int(selection)
    if selection == 0:
        sys.exit(0)

    if selection > 0 and selection <= len(options):
        return options[selection - 1]

    sys.stderr.write("Please select one of the presented options\n")
    return prompt_user(prompt_string, options)
