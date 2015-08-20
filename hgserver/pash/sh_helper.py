#! /usr/bin/python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import sys, subprocess, shlex

def run_command(command_string, input=None, verbose=False):
    subcommand = None
    output_lines = []
    fixed_command_string = command_string.lstrip().rstrip()
    line_cnt = 0
    if(verbose):
        # Don't do any redirection of stdout/stderr
        out_fd=None
        print "EXEC [%s]" % fixed_command_string
    else:
        # all output goes to /dev/null
        out_fd = open('/dev/null', 'w')
    command_end = fixed_command_string.find("|")
    if command_end > 0:
        subcommand = subprocess.Popen(
            shlex.split(fixed_command_string[:command_end]),
            stdin=input, stderr=out_fd, stdout=subprocess.PIPE)
        return(run_command(fixed_command_string[command_end + 1:], input = subcommand.stdout))
    else:
        subcommand = subprocess.Popen(shlex.split(fixed_command_string),
                                      stdin=input, stderr=out_fd, stdout=subprocess.PIPE)
    while True:
        l = subcommand.stdout.readline()
        if not l:
            if verbose:
                print "Breaking after reading %i lines from subprocess" % line_cnt
            break
        if verbose:
            print l,
            output_lines.append(l.rstrip())
    if(not verbose):
        out_fd.close()
    return output_lines

def prompt_user(prompt_string, options, period=True):
    index = 0
    print
    print '0) Exit.'
    for option in options:
        index += 1
        s = '%s) %s' % (index, option)
        if period:
            s += '.'
        print s
    print
    selection = raw_input(prompt_string + ' ')
    if selection.isdigit():
        selection = int(selection)
        if(selection == 0):
            sys.exit(0)
        if(selection > 0 and selection <= index):
            return options [selection - 1]
        else:
            sys.stderr.write('Please select one of the presented options\n')
    else:
        sys.stderr.write('Please select the number corresponding to the option\n')
    return prompt_user(prompt_string, options)

