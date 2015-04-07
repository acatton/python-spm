#!/usr/bin/env python
# Copyright (c) 2015 Antoine Catton
# See the LICENSE.txt file.

import tempfile
import os
import unittest
import subprocess

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
        env = run('env', env={'FOO': 'BAR'}).stdout.read().split('\n')

        assert 'FOO=BAR' in env

    def test_empty_environment(self):
        env = run('env', env=empty_environ()).stdout.read()

        assert env == ''

    def test_repr(self):
        """
        A user should be able to run str(Subprocess) in their shell prompt.
        """
        cmd_str = str(run('echo', '-n', 'foo"bar'))
        output = subprocess.check_output(cmd_str, shell=True)

        assert output == 'foo"bar'

    def test_repr_env(self):
        cmd_str = str(run('env', env={'FOO': 'BAR'}))
        env = subprocess.check_output(cmd_str, shell=True).split('\n')

        assert 'FOO=BAR' in env

    def test_empty_env(self):
        proc = run('env', env=empty_environ(foo='bar'))

        spm_run = set(proc.stdout.read().split('\n'))
        sh_run = set(subprocess.check_output(str(proc), shell=True).split('\n'))

        assert sh_run == spm_run

    def test_subprocess_failure(self):
        with self.assertRaises(subprocess.CalledProcessError):
            run('false').wait()


class PipeTest(TempFileMixin, unittest.TestCase):
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

if __name__ == '__main__':
    unittest.main()
