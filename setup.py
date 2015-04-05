import os
from setuptools import setup
from setuptools.command.test import test as TestCommand


def read(fname):
    dirname = os.path.dirname(__file__)
    with open(os.path.join(fname), 'r') as file_:
        return file_.read()


class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        pytest.main(self.test_args)

version = '0.9.0'

setup(name='spm',
      version=version,
      description=("SubProcess Manager provides a simple programming interface "
                   "to safely run, pipe and redirect output of subprocesses."),
      long_description=read('README.rst'),
      keywords=("api exec execute fork output pipe process processes redirect "
                "safe sh shell subprocess"),

      author="Antoine Catton",
      author_email="devel at antoine dot catton dot fr",

      license="MIT",
      url="https://github.com/acatton/python-spm",
      classifiers=[
          "Development Status :: 4 - Beta",
          "Environment :: Console",
          "Intended Audience :: Developers",
          "Intended Audience :: System Administrators",
          "License :: OSI Approved :: MIT License",
          "Operating System :: POSIX",
          "Programming Language :: Python :: 2.7",
          "Programming Language :: Python :: 3.3",
          "Programming Language :: Python :: 3.4",
          "Programming Language :: Unix Shell",
          "Topic :: System :: System Shells",
      ],

      packages=['spm'],
      install_requires=[
          'six',
      ],
      tests_require=[
          'pytest',
      ],
      cmdclass={'test': PyTest},
)
