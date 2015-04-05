# -*- coding: utf-8 -*-
# Copyright (c) 2015 Antoine Catton
# See the LICENSE file.

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

# Types with only one instance of it
stdin = type('stdin_redirect', (object, ), {})()
stdout = type('stdout_redirect', (object, ), {})()
stderr = type('stderr_redirect', (object, ), {})()
empty_environ = type('empty_environ', (dict, ), {})()


@six.python_2_unicode_compatible
class Subprocess(object):
    def __init__(self, args, stdin=None, stdout=None, stderr=None, env=None):
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
                      stdout=subprocess.PIPE,
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

        return kwargs

    @property
    def stdout(self):
        return self._process.stdout

    @property
    def stdin(self):
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
        self._process.poll()
        return self._process.returncode

    def __str__(self):
        ret = ''

        if isinstance(self._stdin, Subprocess):
            ret += str(self._stdin) + ' | '

        ret += ' '.join(self._args)
        return ret

    def __repr__(self):
        return '<Subprocess {!r}>'.format(name, str(self))

    def pipe(self, *args):
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
            otherprocess = run(*args)

        otherprocess.stdin = self
        return otherprocess


def run(*args, **kwargs):
    """
    Run a simple subcommand::

        >>> print(run('echo', '-n', 'hello world').stdout.read().decode())
        hello world
    """
    return Subprocess(args)


def pipe(arg_list):
    """
    Pipe many commands::

        >>> noop = pipe([['gzip'], ['gzip'], ['zcat'], ['zcat']])
        >>> noop.stdin.write('foo')
        >>> noop.stdin.close()
        >>> print(noop.stdout.read().decode())
        foo
    """
    if len(arg_list) == 0:
        raise ValueError("arg_list needs at least one item")

    cmd, arg_list = arg_list[0], arg_list[1:]

    acc = run(*cmd)
    for cmd in arg_list:
        acc = acc.pipe(*cmd)
    return acc
