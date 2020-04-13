bionorm
=======
``bionorm`` normalizes and validates genomic data files prior to further processing
or inclusion in a data store such as that of the
`Legume Federation <https://www.legumefederation.org/en/data-store/>`_.

Prerequisites
-------------
Python 3.6 or greater is required.
This package is tested under Linux and MacOS using Python 3.7.

Installation for Users
----------------------
Install via pip or (better yet) `pipx <https://pipxproject.github.io/pipx/>`_: ::

     pipx install bionorm

``bionorm`` contains some long commands and many options.  To enable command-line
completion for ``bionorm`` commands, execute the following command if you are using
``bash`` as your shell: ::

    eval "$(_BIONORM_COMPLETE=source_bash bionorm)"

For Developers
--------------
If you plan to develop ``bionorm``, you'll need to install
the `poetry <https://python-poetry.org>`_ dependency manager.
If you haven't previously installed ``poetry``, execute the command: ::

    curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python

Next, get the master branch from GitHub ::

	git clone https://github.com/legumeinfo/bionorm.git

Change to the ``bionorm/`` directory and install with poetry: ::

	poetry install -v

Run ``bionorm`` with ``poetry``: ::

    poetry run bionorm

Usage
-----
Installation puts a single script called ``bionorm`` in your path.  The usage format is::

    bionorm [GLOBALOPTIONS] COMMAND [COMMANDOPTIONS][ARGS]

Global Options
--------------
The following options are global in scope and, if used, must be placed before
``COMMAND``. Not all commands support every global option:

============================= ====================================================
    --verbose/-v              Log debugging info to stderr.
    --quiet/-q                Suppress logging to stderr.
    --no_log                  Suppress logging to file.
    --progress                Show a progress bar.
    --first_n                 Process only this many records. [default: all]
    --warnings_as_errors/-e   Warnings cause exceptions.
============================= ====================================================

Commands
--------
A listing of commands is available via ``bionorm --help``.
The currently implemented commands are:

============================= ====================================================
  prefix_fasta                Prefix FASTA files for data store standard.
  prefix_gff                  Prefix and sort GFF3 file for data store standard.
  busco                       Perform BUSCO checks.
  detector                    Detect/correct incongruencies among files.
  fasta                       Check for GFF/FASTA consistency.
  generate_readme             Generates a README file with details of genome.
  index                       Indexes FASTA file.
============================= ====================================================

Each command has its ``COMMANDOPTIONS``, which may be listed with: ::

    bionorm COMMAND --help

Project Status
--------------
+-------------------+------------+------------+
| Latest Release    | |pypi|     | |bionorm|  |
+-------------------+------------+            +
| GitHub            | |repo|     |            |
+-------------------+------------+            +
| License           | |license|  |            |
+-------------------+------------+            +
| Travis Build      | |travis|   |            |
+-------------------+------------+            +
| Coverage          | |coverage| |            |
+-------------------+------------+            +
| Code Grade        | |codacy|   |            |
+-------------------+------------+            +
| Dependencies      | |depend|   |            |
+-------------------+------------+            +
| Pre-commit        | |precommit||            |
+-------------------+------------+            +
| Issues            | |issues|   |            |
+-------------------+------------+------------+

.. |bionorm| image:: docs/normal.jpg
     :alt: Make me NORMAL, please!

.. |pypi| image:: https://img.shields.io/pypi/v/bionorm.svg
    :target: https://pypi.python.org/pypi/bionorm
    :alt: Python package

.. |repo| image:: https://img.shields.io/github/commits-since/legumeinfo/bionorm/0.1.0.svg
    :target: https://github.com/legumeinfo/bionorm
    :alt: GitHub repository

.. |license| image:: https://img.shields.io/badge/License-BSD%203--Clause-blue.svg
    :target: https://github.com/legumeinfo/bionorm/blob/master/LICENSE.txt
    :alt: License terms

.. |travis| image:: https://img.shields.io/travis/legumeinfo/bionorm.svg
    :target:  https://travis-ci.org/legumeinfo/bionorm
    :alt: Travis CI

.. |codacy| image:: https://api.codacy.com/project/badge/Grade/b23fc0c167fc4660bb649320e14dac7f
    :target: https://www.codacy.com/gh/legumeinfo/bionorm?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=legumeinfo/bionorm&amp;utm_campaign=Badge_Grade
    :alt: Codacy.io grade

.. |coverage| image:: https://codecov.io/gh/legumeinfo/bionorm/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/legumeinfo/bionorm
    :alt: Codecov.io test coverage

.. |precommit| image:: https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white
    :target: https://github.com/pre-commit/pre-commit
    :alt: pre-commit

.. |issues| image:: https://img.shields.io/github/issues/legumeinfo/bionorm.svg
    :target:  https://github.com/legumeinfo/bionorm/issues
    :alt: Issues reported


.. |depend| image:: https://api.dependabot.com/badges/status?host=github&repo=legumeinfo/bionorm
     :target: https://app.dependabot.com/accounts/legumeinfo/repos/236847525
     :alt: dependabot dependencies
