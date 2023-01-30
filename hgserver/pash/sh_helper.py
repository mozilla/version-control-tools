# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import print_function

import shlex
import subprocess
import sys


def run_command(command_string, input=None):
    subcommand = None
    output_lines = []
    fixed_command_string = command_string.lstrip().rstrip()

    # all output goes to /dev/null
    out_fd = open("/dev/null", "w")

    command_end = fixed_command_string.find("|")
    if command_end > 0:
        subcommand = subprocess.Popen(
            shlex.split(fixed_command_string[:command_end]),
            stdin=input,
            stderr=out_fd,
            stdout=subprocess.PIPE,
        )
        return run_command(
            fixed_command_string[command_end + 1 :], input=subcommand.stdout
        )
    else:
        subcommand = subprocess.Popen(
            shlex.split(fixed_command_string),
            stdin=input,
            stderr=out_fd,
            stdout=subprocess.PIPE,
        )
    while True:
        l = subcommand.stdout.readline()
        if not l:
            break

    out_fd.close()
    return output_lines


def prompt_user(prompt_string, options, period=True):
    index = 0
    print("")
    print("0) Exit.")
    for option in options:
        index += 1
        s = "%s) %s" % (index, option)
        if period:
            s += "."
        print(s)
    print("")
    selection = input(prompt_string + " ")
    if selection.isdigit():
        selection = int(selection)
        if selection == 0:
            sys.exit(0)
        if selection > 0 and selection <= index:
            return options[selection - 1]
        else:
            sys.stderr.write("Please select one of the presented options\n")
    else:
        sys.stderr.write("Please select the number corresponding to the option\n")
    return prompt_user(prompt_string, options)
