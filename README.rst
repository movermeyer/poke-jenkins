poke-jenkins: Mercurial extension for triggering jenkins jobs
=============================================================

The ``poke-jenkins`` is a Mercurial extension that for the heads of an incoming changeset starts a Jenkins job.

.. image:: https://api.travis-ci.org/paylogic/poke-jenkins.png
   :target: https://travis-ci.org/paylogic/poke-jenkins
.. image:: https://pypip.in/v/poke-jenkins/badge.png
   :target: https://crate.io/packages/poke-jenkins/
.. image:: https://coveralls.io/repos/paylogic/poke-jenkins/badge.png?branch=master
   :target: https://coveralls.io/r/paylogic/poke-jenkins


Installation
------------

.. sourcecode::

    pip install poke-jenkins


Configuration
-------------

An example of .hg/hgrc of your remote repository:

.. code-block:: cfg

    [extensions]
    poke_jenkins =

    [poke_jenkins]

    # Jenkins url
    jenkins_base_url = http://ci.example.com

    # List the jobs you want to start
    jobs = Project_Tests_Dev Project_Coverage_Dev

    # Feel free to change this parameter
    tag = foo

    # The url which Jenkins will use to clone the repository
    repo_url = ssh://code.example.com//example

    # Timeout in seconds
    timeout = 10

    # Jenkins user id
    username = foo

    # Jenkins API Token
    password = bar

    # Branch regular expression filter
    branch_regex = ^c\d{4}


Usage
-----

With given configuration above, it will call jenkins jobs to start builds:

* http://ci.example.com/job/Project_Tests_Dev?TAG=foo&NODE_ID=<mercurial commit hash>&BRANCH=<branch name>&REPO_URL=ssh://code.example.com//example

* http://ci.example.com/job/Project_Coverage_Dev?TAG=foo&NODE_ID=<mercurial commit hash>&BRANCH=<branch name>&REPO_URL=ssh://code.example.com//example

It will add basic auth headers to authenticate the calls if username and password settings are set.


Python3 support
---------------

Package itself supports python3 out of the box, but not mercurial ATM.


Contact
-------

If you have questions, bug reports, suggestions, etc. please create an issue on
the `GitHub project page <http://github.com/paylogic/poke-jenkins>`_.


License
-------

This software is licensed under the `MIT license <http://en.wikipedia.org/wiki/MIT_License>`_

See `<LICENSE.txt>`_

© 2013 Paylogic International.
