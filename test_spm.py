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

        assert six.b(cat.stdout.read()) == content


class PipeTest(TempFileMixin, unittest.TestCase):
    def test_stdin_from_file(self):
        content = '__file_content__'

        fname = self.get_temp_filename()
        with open(fname, 'w') as file_:
            file_.write(content)

if __name__ == '__main__':
    unittest.main()
