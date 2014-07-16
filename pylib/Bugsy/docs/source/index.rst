.. Bugzilla documentation master file, created by
   sphinx-quickstart on Sat May 31 20:43:30 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Bugsy!
=================

Bugsy is a tool that allows you to programmatically work with Bugzilla using its native REST API.

To use you will do

.. code-block:: python

    import bugsy
    bugzilla = bugsy.Bugsy()
    bug = bugzilla.get(123456)
    bug123456.status = 'RESOLVED'
    bug123456.resolution = 'FIXED'
    bugzilla.put(bug123456)

Installing Bugsy
----------------

To install Bugsy, simply use pip or easy install

Pip

.. code-block:: bash

    pip install bugsy


easy_install

.. code-block:: bash

    easy_install bugsy

Using Bugsy
-----------

Getting a bug from Bugzilla
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Getting a bug is quite simple. Create a Bugsy object and then get the bug
number that you want.

.. code-block:: python

    import bugsy
    bugzilla = bugsy.Bugsy()
    bug = bugzilla.get(123456)

Creating a new bug
~~~~~~~~~~~~~~~~~~

To create a new bug, create a Bug object, populate it with the items that you need and then
use the Bugsy object to put the bug into Bugzilla

.. code-block:: python

    import bugsy
    bug = bugsy.Bug()
    bug.summary = "I really realy love cheese"
    bug.add_comment("and I really want sausages with it!")

    bugzilla = bugsy.Bugsy("username", "password")
    bugzilla.put(bug)
    bug.id #returns the bug id from Bugzilla


Searching Bugzilla
~~~~~~~~~~~~~~~~~~

To search for bugs you will need to create a :class:`Bugsy` object and then you can call
`search_for` and chain the search. The :class:`Search` API is a `Fluent API <https://en.wikipedia.org/wiki/Fluent_interface>`_
o you just chain the items that you need and then call `search` when the search is complete.

.. code-block:: python

    import bugsy
    bugzilla = bugsy.Bugsy()
    bugs = bugzilla.search_for\
                    .keywords("checkin-needed")\
                    .include_fields("flags")\
                    .search()

More details can be found in from the :class:`Search` class

Comments
~~~~~~~~

Getting comments from a bug

.. code-block:: python

    import bugsy
    bugzilla = bugsy.Bugsy()
    bug = bugzilla.get(123456)
    comments = bug.get_comments()
    comments[0].text # Returns  "I <3 Sausages"

Adding comments to a bug

.. code-block:: python

    import bugsy
    bugzilla = bugsy.Bugsy()
    bug = bugzilla.get(123456)
    bug.add_comment("And I love bacon too!")

To see further details look at:

.. toctree::
   :maxdepth: 2

   bugsy.rst
   bug.rst
   comment.rst
   search_bug.rst


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. _Bugsy: