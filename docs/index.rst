python-spm (Sub Process Manager) documentation
==============================================

Install::

    pip install spm

Use:

.. code-block:: python

    >>> from spm import run, pipe, empty_environ
    >>> run('cat', '/etc/passwd')
    <Subprocess 'cat /etc/passwd'>
    >>> run('cat', '/etc/passwd').pipe('grep', 'jdoe')
    <Subprocess 'cat /etc/passwd | grep jdoe'>
    >>> pipe(['gzip', '-c', '/etc/passwd'], ['zcat'])
    <Subprocess 'gzip -c /etc/passwd | zcat'>
    >>> run('git', 'commit', env={'GIT_COMMITTER_NAME': 'John Doe'})
    <Subprocess "env 'GIT_COMMITTER_NAME=John Doe' git commit">
    >>> run('ls', env=empty_environ())
    <Subprocess 'env - ls'>
    >>> run('ls', env=empty_environ({'FOO': 'BAR'}))
    <Subprocess 'env - FOO=BAR ls'>
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




Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

