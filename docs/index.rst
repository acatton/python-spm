python-spm (Sub Process Manager) documentation
==============================================

.. image:: https://travis-ci.org/acatton/python-spm.svg?branch=master
    :target: https://travis-ci.org/acatton/python-spm

Install::

    pip install spm

Use:

.. doctest::

    >>> from spm import run, pipe, propagate_env
    >>> run('cat', '/etc/passwd')
    <Subprocess 'env - cat /etc/passwd'>
    >>> run('cat', '/etc/passwd').pipe('grep', 'jdoe')
    <Subprocess 'env - cat /etc/passwd | env - grep jdoe'>
    >>> pipe(['gzip', '-c', '/etc/passwd'], ['zcat'])
    <Subprocess 'env - gzip -c /etc/passwd | env - zcat'>
    >>> run('git', 'commit', env={'GIT_COMMITTER_NAME': 'John Doe'})
    <Subprocess "env - 'GIT_COMMITTER_NAME=John Doe' git commit">
    >>> run('ls', env=propagate_env())
    <Subprocess 'ls'>
    >>> run('ls', env=propagate_env({'FOO': 'BAR'}))
    <Subprocess 'env FOO=BAR ls'>
    >>> run('echo', '-n', 'foo').wait()
    ('foo', None)
    >>> run('echo', '-n', 'bar').stdout.read()
    'bar'
    >>> noop = run('gzip').pipe(run('zcat'))  # = run('gzip').pipe('zcat')
    >>> run('echo', '-n', 'example').pipe(noop).stdout.read()
    'example'

Go further:

.. toctree::
   :maxdepth: 2

   security
   usage




Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

