.. _sec_testing:

=======
Testing
=======

All code should be tested. That is easily said, sometimes hard to do.
But with pyramid it is possible.

For every basic function, for every view (or related group of views),
there should be tests.


Test Frameworks
---------------

We use a combination of *Unit* tests, *Webtest* and *Selenium/webdriver* tests.
Each have their pros and cons.


Selenium / webdriver
~~~~~~~~~~~~~~~~~~~~

Selenium tests for example require not only the webapp to be started
but also need a browser to be fired up and controlled remotely.
While this might take longer than other flavours of tests,
it does enable some interesting techniques like taking screenshots.
Apart from Firefox and Chrome there are more lightweight alternatives
like PhantomJS (a headless webkit browser that handles javascript quite well).


Webtest
~~~~~~~

Webtest tests are a lot quicker and still high level enough to allow for
testing the webapp almost like using a browser.


Unit Tests
~~~~~~~~~~

Unit tests are the optimum when it comes to speed.
They test small and smallest units of code,
e.g. check if some input to a function will produce a given output.


Test Layout
-----------

Test code should reside in a folder *tests/*
relative to the modules containing the code under test
and in files starting with *test_*.


Running the Tests
-----------------

The entire set of tests can be run with *nose*:
::

   env/bin/nosetests c3smembership/

As this takes several minutes, it is a good idea to run single tests or groups
of tests individually during development of a certain part of the code.

Moreover, to see whether your test code does what it is supposed to do,
you need to run it separated fromm the other tests,
so you don't happen to get coverage from other code or tests.

You may choose either a single test module or even a single test:
::

   # all model tests
   $ env/bin/nosetests c3smembership/tests/test_models.py
   ..................................
   ----------------------------------------------------------------------
   Ran 34 tests in 6.107s

   OK

   # one suite of tests:
   $ env/bin/nosetests c3smembership/tests/test_models.py:C3sMembershipModelTests
   .............
   ----------------------------------------------------------------------
   Ran 13 tests in 2.668s

   OK

   # one specific test:
   $ env/bin/nosetests c3smembership/tests/test_models.py:C3sMembershipModelTests.test_get_by_code
   .
   ----------------------------------------------------------------------
   Ran 1 test in 0.221s

   OK

.. note:: There are some settings for running the tests in **setup.cfg**.
   Look at the section starting with **[nose]**

   * you may stop testing upon first error or failure
   * you may start a debugger upon first error or failure
   * many more options

Code Coverage
-------------

We also look at **coverage** to see if the tests touched all code.

.. note:: There are some settings for coverage.py in **setup.cfg**.
   Look at the section starting with **[coverage:run]**

   * you may omit files if you don't want them covered
   * many more options


Continuous Integration
----------------------

We have a Jenkins instance run our codes tests after every new commit.

This way, even if a developer forgets to run all the tests
before pushing to the repositories, the newly introduced code
as well as all the old code are tested to ensure
that all relevant functionality is preserved.


Test Documentation
------------------

The documentation particles below are generated from the docstrings in the
actual Python test code. 


.. toctree::
   :maxdepth: 2
   :glob:

   *
