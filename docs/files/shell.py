#!/usr/bin/env python3
# Copyright (C) 2015 Antoine Catton
# Licensed under WTFPL <http://www.wtfpl.net/>

import shlex
import os
import sys

NORMAL_PIDWAIT = 0  # Just hardcoded variable you can ignore that


def lookup(command):
    """
    Lookup a command in PATH. For example::

        >>> lookup('ls')
        '/usr/bin/ls'
        >>> lookup('usermod')
        '/usr/sbin/usermod'
        >>> lookup('foobar')
        Traceback (most recent call last):
          File "<stdin>", line 1, in <module>
        ValueError: Invalid command

    This function is incredibly dumb, and does not search for an executable
    file.
    """
    for path in os.environ.get('PATH', '').split(':'):
        fname = os.path.join(path, command)
        if os.path.exists(fname):
            return fname
    raise ValueError("Invalid command")


def run(line):
    """
    Run a shell line: run('ls /tmp') will execv('/usr/bin/ls', ['ls', '/tmp'])
    """
    arguments = shlex.split(line)
    path = lookup(arguments[0])  # Lookup the first arguments in PATH
    execute(path, arguments)


def execute(path, arguments):
    """
    Wrapper around execv():

    * fork()s before exec()ing (in order to run the command in a subprocess)
    * wait for the subprocess to finish before returning (blocks the parent
      process)

    This is **hyper** simplistic. This *does not* handle **many** edge cases.

    *DO NOT DO THIS*: subprocess.check_call() does it better, and handle edge
    cases.
    """
    pid = os.fork()
    if pid == 0:
        try:
            os.execv(path, arguments)
        finally:
            sys.exit(1)  # In case path is not executable
    else:
        try:
            # Wait for subprocess to finish
            os.waitpid(pid, NORMAL_PIDWAIT)
        except OSError:
            pass  # The subprocess was already finish
        return

if __name__ == '__name__':

    while True:
        line = input('$ ')

        if line.strip() == 'exit':  # Wants to exit the shell
            break

        run(line)
