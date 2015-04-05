#!/usr/bin/env python
# Copyright (c) 2015 Antoine Catton
# See the LICENSE.txt file.

import tempfile
import os
import unittest

import six
from spm import run, pipe

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


class PipeTest(TempFileMixin, unittest.TestCase):
    def test_stdin_from_file(self):
        content = '__file_content__'

        fname = self.get_temp_filename()
        with open(fname, 'w') as file_:
            file_.write(content)

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
