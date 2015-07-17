Usage
=====

.. testsetup:: *

    from spm import run, pipe, update_environ

Installation
------------

From cheeseshop
^^^^^^^^^^^^^^^

::

    pip install spm

From source
^^^^^^^^^^^

::

    git clone git://github.com/acatton/python-spm spm
    pip install -e ./spm


Learn by example
----------------

You can reduce spm to two function ``run()`` and ``pipe()``. But the objects
returned by these two functions have many useful methods.

Run subcommands
^^^^^^^^^^^^^^^

.. doctest::

    >>> stdout, stderr = run('echo', 'Hello, World').wait()
    >>> stdout
    'Hello, World\n'
    >>> stdout, stderr = run('false').wait()
    Traceback (most recent call last):
      ...
    subprocess.CalledProcessError: Command 'false' returned non-zero exit status 1


``run()`` create a subprocess, but it doesn't spawn it yet. ``wait()`` spawn is
one way to spawn the said subprocess.

You can also read its output:

.. doctest::

    >>> run('echo', 'Hello, World').stdout.read()
    'Hello, World\n'


Pipe subprocesses together
^^^^^^^^^^^^^^^^^^^^^^^^^^

Piping is done with ``pipe()``.

``pipe()`` accepts either an argument list or a ``Subprocess``. ``pipe()`` is
also a method on ``Subprocess``.

.. doctest::

    >>> data, _ = pipe(['echo', '-n', 'Hello World'], ['bzip2']).wait()
    >>> import bz2
    >>> bz2.decompress(data)
    'Hello World'


Redirect output to a file
^^^^^^^^^^^^^^^^^^^^^^^^^

You can set ``Subprocess.stdout`` to an open file. ``spm`` will be in charge of
closing it.

.. doctest::

    >>> proc = run('echo', 'Hello World')
    >>> import os
    >>> proc.stdout = open(os.devnull, 'w')
    >>> proc.wait()
    (None, None)


Propagate the environment
^^^^^^^^^^^^^^^^^^^^^^^^^

You can use the keyword argument ``env`` on ``run()`` or ``pipe()`` in order to
override some variable in the environment of the subprocess.

.. doctest::

    >>> run('env').stdout.read()
    ''
    >>> run('env', env={'FOO': 'BAR'}).stdout.read()
    'FOO=BAR\n'

For security reasons, the environment doesn't get propagated to the subprocess.
See :ref:`environment_propagation_security`.

The class ``update_environ`` (but you should think of it as a function) will propagate the environment, and update it if you pass it

.. doctest::

    >>> run('env', env=update_environ()).stdout.read().decode() != ''
    True
    >>> 'a=b' in run('env', env=update_environ(a='b')).stdout.read().split('\n')
    True
    >>> 'FOO=BAR' in run('env', env=update_environ({'FOO': 'BAR'})).stdout.read().split('\n')
    True



Debug your subprocesses
^^^^^^^^^^^^^^^^^^^^^^^

You can debug your subprocesses and try to running manually by getting their
representation or converting them to strings.

Copying and pasting the string in your terminal should have exact the same
result than calling ``wait()``.

.. doctest::

    >>> print(run('echo', 'Hello'))
    env - echo Hello
    >>> print(run('echo', 'Hello, World'))
    env - echo 'Hello, World'
    >>> run('echo', '$NAME')
    <Subprocess "env - echo '$NAME'">

Create command functions
^^^^^^^^^^^^^^^^^^^^^^^^

You can also create a ``git()`` function if you wanted. This could be done
thanks to ``functools.partial()``.

.. doctest::

    >>> from functools import partial
    >>> git = partial(run, 'git')
    >>> git('commit')
    <Subprocess 'env - git commit'>
    >>> git('archive', '--output=/tmp/archive.tar.gz')
    <Subprocess 'env - git archive --output=/tmp/archive.tar.gz'>

API
---

.. autoclass:: spm.Subprocess(args, env=None)
   :members: stdout, stdin, returncode, wait, pipe
   :undoc-members: __init__

.. autofunction:: spm.run

.. autofunction:: spm.pipe
