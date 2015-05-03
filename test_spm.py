#!/usr/bin/env python
# Copyright (c) 2015 Antoine Catton
# See the LICENSE.txt file.

import tempfile
import os
import unittest
import subprocess
import contextlib
import signal

import six
from spm import run, pipe, empty_environ

class TempFileMixin(object):
    def setUp(self):
        super(TempFileMixin, self).setUp()
        self._tempfiles = []

    def get_temp_filename(self):
        fd, fname = tempfile.mkstemp()
        os.close(fd)
        return fname

    def tearDown(self):
        for fname in self._tempfiles:
            os.remove(fname)


class DeadLockMixin(object):
    @contextlib.contextmanager
    def assertDoesNotHang(self, timeout=2):

        def handler(signum, frame):
            assert False, "Hanged for more than {} seconds".format(timeout)

        signal.signal(signal.SIGALRM, handler)
        try:
            signal.alarm(timeout)
            yield
        finally:
            signal.signal(signal.SIGALRM, signal.SIG_DFL)


class RunTest(TempFileMixin, unittest.TestCase):
    def test_stdin_from_file(self):
        content = '__file_content__'

        fname = self.get_temp_filename()
        with open(fname, 'w') as file_:
            file_.write(content)

        cat = run('cat')
        cat.stdin = open(fname)

        assert cat.stdout.read().decode() == content

    def test_stdout_to_file(self):
        string = '__output__'

        fname = self.get_temp_filename()

        echo = run('echo', '-n', string)
        echo.stdout = open(fname, 'w')
        out, err = echo.wait()

        assert out is None

        with open(fname) as file_:
            assert six.u(file_.read()) == string

    def test_environment(self):
        env = run('env', env={'FOO': 'BAR'}).stdout.read().decode().split('\n')

        assert 'FOO=BAR' in env

    def test_empty_environment(self):
        env = run('env', env=empty_environ()).stdout.read().decode()

        assert env == ''

    def test_repr(self):
        """
        A user should be able to run str(Subprocess) in their shell prompt.
        """
        cmd_str = str(run('echo', '-n', 'foo"bar'))
        output = subprocess.check_output(cmd_str, shell=True).decode()

        assert output == 'foo"bar'

    def test_repr_env(self):
        cmd_str = str(run('env', env={'FOO': 'BAR'}))
        env = subprocess.check_output(cmd_str, shell=True).decode().split('\n')

        assert 'FOO=BAR' in env

    def test_empty_env(self):
        proc = run('env', env=empty_environ(foo='bar'))

        spm_run = set(proc.stdout.read().decode().split('\n'))
        sh_run = set(
            subprocess.check_output(str(proc), shell=True).decode().split('\n')
        )

        assert sh_run == spm_run

    def test_subprocess_failure(self):
        with self.assertRaises(subprocess.CalledProcessError):
            run('false').wait()

    def test_environement_on_pipe(self):
        proc = pipe(['env'], ['egrep', '^FOO='], env={'FOO': 'BAR'})

        assert proc.stdout.read().decode() == 'FOO=BAR\n'

    def test_pass_subprocess_to_pipe(self):
        proc = pipe(['echo', '-n', 'hello'], ['gzip'], run('zcat'))
        assert proc.stdout.read().decode() == 'hello'


class PipeTest(DeadLockMixin, TempFileMixin, unittest.TestCase):
    def test_stdin_from_file(self):
        content = '__file_content__'

        fname = self.get_temp_filename()
        with open(fname, 'w') as file_:
            file_.write(content)

        cat = run('gzip').pipe('zcat')
        cat.stdin = open(fname)

        assert cat.stdout.read().decode() == content

    def test_stdout_to_file(self):
        string = '__output__'
        fname = self.get_temp_filename()

        echo = run('echo', '-n', string)
        echo.stdout = open(fname, 'w')
        out, err = echo.wait()

        assert out is None

        with open(fname) as file_:
            assert six.u(file_.read()) == string

    def test_safe_pipe_stdout_read(self):
        command = pipe(['gzip'], ['zcat'])

        with self.assertDoesNotHang():
            assert command.stdout.read().decode() == ''  # No deadlock

    def test_safe_pipe_wait(self):
        command = pipe(['gzip'], ['zcat'])

        with self.assertDoesNotHang():
            out, _ = command.wait()  # No deadlock

        assert out.decode() == ''

    def test_failing_pipe_command(self):
        with self.assertRaises(subprocess.CalledProcessError):
            pipe(['true'], ['false'], ['true']).wait()

if __name__ == '__main__':
    unittest.main()
