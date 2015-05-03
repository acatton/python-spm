# -*- coding: utf-8 -*-
# Copyright (c) 2015 Antoine Catton
# See the LICENSE file.

import os
import subprocess

import six


class _LazyPopen(object):
    """
    Invoke Popen only when getting an attribute.

    This is internal to spm library.
    """
    def __init__(self, parent):
        self._parent = parent
        self._wrapped = None

    @property
    def is_running(self):
        if self._wrapped is None:
            return False
        else:
            return self.poll() is None

    def __getattribute__(self, name):
        if name in ('_parent', '_wrapped', 'is_running'):
            return super(_LazyPopen, self).__getattribute__(name)
        else:
            if self._wrapped is None:
                kwargs = self._parent._get_popen_kwargs()
                self._wrapped = subprocess.Popen(**kwargs)

            return getattr(self._wrapped, name)


class _LazyPopenAttribute(object):
    def __init__(self, obj, attr):
        self._obj = obj
        self._attr = attr
        self._wrapped = None

    def __getattribute__(self, name):
        if name in ('_obj', '_attr', '_wrapped'):
            return super(_LazyPopenAttribute, self).__getattribute__(name)
        else:
            if self._wrapped is None:
                self._wrapped = getattr(self._obj, self._attr)
                self._obj._parent._get_popen_attr()

            return getattr(self._wrapped, name)


# Types with only one instance of it
stdin = type('stdin_redirect', (object, ), {})()
stdout = type('stdout_redirect', (object, ), {})()
stderr = type('stderr_redirect', (object, ), {})()
empty_environ = type('empty_environ', (dict, ), {})


@six.python_2_unicode_compatible
class Subprocess(object):
    """
    Subprocess object used to access properties of the subprocess such as its
    returncode.

    You shouldn't have to instanciate this class. ``run()`` and ``pipe()`` will
    do it for you.
    """

    def __init__(self, args, stdin=None, stdout=None, stderr=stderr, env=None):
        if env is None:
            env = {}  # Default argument

        self._stdin = stdin
        self._stdout = stdout
        self._stderr = stderr
        self._env = env
        self._args = args
        self._process = _LazyPopen(self)

    def _get_popen_kwargs(self):
        kwargs = dict(args=self._args,
                      )

        if self._stdin is None:
            kwargs.update(stdin=subprocess.PIPE)
        elif isinstance(self._stdin, Subprocess):
            kwargs.update(stdin=self._stdin.stdout)
        elif hasattr(self._stdin, 'fileno'):  # File-like object
            kwargs.update(stdin=self._stdin)
        else:
            raise TypeError("stdin can't be anything else than another process "
                            "or a file")

        if self._stdout is None:
            kwargs.update(stdout=subprocess.PIPE)
        elif hasattr(self._stdout, 'fileno'):  # File-like object
            kwargs.update(stdout=self._stdout)
        else:
            raise TypeError("stdout can't be anything else than a file.")

        if isinstance(self._env, empty_environ):
            kwargs.update(env=self._env.copy())
        elif isinstance(self._env, dict):
            if len(self._env) > 0:
                environ = os.environ.copy()
                environ.update(self._env)
                kwargs.update(env=environ)
        else:
            raise TypeError("env has to be a dictionnary.")

        return kwargs

    def _get_popen_attr(self):
        if isinstance(self._stdin, Subprocess):
            self._stdin._process._wrapped.stdout = None
            self._stdin._get_popen_attr()
        elif hasattr(self._process.stdin, 'close'):
            if not self._process.stdin.closed:
                self._process.stdin.flush()
                self._process.stdin.close()

    @property
    def stdout(self):
        """
        Set the stdout of the subprocess. It should be a file. If its ``None``
        it could be read from the main process.
        """
        return _LazyPopenAttribute(self._process, 'stdout')

    @stdout.setter
    def stdout(self, value):
        if self._process.is_running:
            raise RuntimeError("Can't change stdout of a running process")

        self._stdout = value
        getattr(self, 'stdout')  # Force the subprocess to run

    @property
    def stdin(self):
        """
        Set the stdin of the subprocess. It should be a file. If its ``None``
        it will be a pipe to wich you can write from the main process.
        """
        if isinstance(self._stdin, Subprocess):
            return self._stdin.stdin
        else:
            return self._process.stdin

    @stdin.setter
    def stdin(self, value):
        if self._process.is_running:
            raise RuntimeError("Can't attach stdin to a running process")
        elif isinstance(self._stdin, Subprocess):
            self._stdin.stdin = value
        else:
            # Setting any other value than a subprocess to stdin runs the
            # subprocess. This can only be None or a Subprocess if the
            # subprocess isn't running.
            assert self._stdin is None, ("Contact the library developer if you "
                                         "ever hit that case.")
            self._stdin = value

            if not isinstance(value, Subprocess):
                # If the value is something else than a subprocess
                # invoke the process. _LazyPopen.stdout will invoke it.
                getattr(self, 'stdout')

    @property
    def returncode(self):
        """
        Return the the returncode of the subprocess. If the subprocess isn't
        terminated yet, it will return ``None``.
        """
        return self._process.poll()

    def __str__(self):
        ret = ''

        if isinstance(self._stdin, Subprocess):
            ret += str(self._stdin) + ' | '

        if isinstance(self._env, empty_environ):
            env = ('env', '-', )
        elif len(self._env) > 0:
            env = ('env', )
        else:
            env = tuple()

        env += tuple('{}={}'.format(k, v) for k, v in self._env.items())

        ret += ' '.join(six.moves.shlex_quote(i) for i in (env + self._args))
        return ret

    def __repr__(self):
        return '<Subprocess {!r}>'.format(str(self))

    def pipe(self, *args, **kwargs):
        r"""
        Pipe processes together. pipe() can receive an argument list or a
        subprocess.

            >>> print(run('echo', 'foo\nbar').pipe('grep', 'bar').stdout.read()
            ...                                                  .decode())
            bar
            <BLANKLINE>
            >>> noop = run('gzip').pipe('zcat')
            >>> print(noop)
            gzip | zcat
            >>> # This will be: echo -n foo | gzip | zcat
            >>> print(run('echo', '-n', 'foo').pipe(noop).stdout.read()
            ...                                                 .decode())
            foo
        """
        if len(args) == 0:
            raise ValueError("Needs at least one argument")
        elif len(args) == 1 and isinstance(args[0], Subprocess):
            otherprocess = args[0]
            if otherprocess._process.is_running:
                raise ValueError("Can't attach the output to the input of a "
                                 "running process.")
        else:
            otherprocess = run(*args, **kwargs)

        otherprocess.stdin = self
        return otherprocess

    def _wait(self):  # Recursively wait from the beginning of the pipe
        if isinstance(self._stdin, Subprocess):
            self._stdin._process._wrapped.stdout = None  # Hide stdout
            self._stdin._wait()
        return self._process.communicate()

    def wait(self):
        """
        Waits for the subprocess to finish, and then return a tuple of its
        stdout and stderr.

        If there's no error, the stderr is ``None``. If the process fails (has
        a non-zero exit code) it raises a ``subprocess.CalledProcessError``.
        """
        self._process.poll()  # Warmup _LazyPopen of the whole pipe
        output, errors = self._wait()

        proc = self
        while True:  # Go up in the pipe to find out if any subprocess failed
            if proc.returncode != 0:
                raise subprocess.CalledProcessError(
                    proc.returncode, proc, output)

            if isinstance(proc._stdin, Subprocess):
                proc = proc._stdin
            else:
                break  # Exit the loop when we hit the beginning of the pipe

        return output, errors


def run(*args, **kwargs):
    """
    Run a simple subcommand::

        >>> print(run('echo', '-n', 'hello world').stdout.read().decode())
        hello world

    Returns a Subprocess.
    """
    return Subprocess(args, **kwargs)


def pipe(*arguments, **kwargs):
    """
    Pipe many commands::

        >>> noop = pipe(['gzip'], ['gzip'], ['zcat'], ['zcat'])
        >>> _ = noop.stdin.write('foo'.encode())  # Ignore output in Python 3
        >>> noop.stdin.close()
        >>> print(noop.stdout.read().decode())
        foo

    Returns a Subprocess.
    """
    if len(arguments) == 0:
        raise ValueError("arguments needs at least one item")

    cmd, arguments = arguments[0], arguments[1:]

    acc = run(*cmd, **kwargs)
    for cmd in arguments:
        if isinstance(cmd, Subprocess):
            acc = acc.pipe(cmd)
        else:
            acc = acc.pipe(*cmd, **kwargs)
    return acc
