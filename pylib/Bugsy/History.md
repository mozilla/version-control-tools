
0.6.0 / 2015-10-08
==================

  * Update flake8 config to only check the correct items.
  * Fix flake8 errors.
  * Move final requests to use central request and handler methods
  * Move Exception to BugsyException
  * Add more tests for resiliency against HTTP errors during API requests
  * Remove support for Python 2.6. I won't be actively working against it but won't be mindful of errors
  * Fix formatting to work with python 2.6
  * Update error handling for the majority of cases so that it is handled centrally
  * Clean up imports of tests
  * Remove duplication in Exception handling
  * Move Errors to their own file and update imports for others.
  * Move JSON handling into request method
  * Use correct response HTTP code for Bugzilla error handling tests

0.5.0 / 2015-09-26
==================

  * Add the ability to set tags on comments. Fixes #5
  * Add the ability to set and get assignee on a bug. Fixes #17
  * Raise an error when posting a comment and we get a error back from Bugzilla. Fixes #25
  * Raise an exception when `get()` is called and Bugzilla can not return it. Fixes #24
  * Add configuration for flake8
  * Improve the docs & examples for add_comment()
  * Make sure the docs index page is listed in the sidebar table of contents
  * Make sure Sphinx autodoc generates docs for Class __init__ methods
  * Make the Bugsy PyPI page link to GitHub
  * Add Bugzilla API keys support
  * fix unit tests by using all defaults include_fields into requests
  * include whiteboard when pulling bug data from bugzilla
  * add test coverage link in README.md
  * Add unit test coverage report on coveralls
  * create documented properties for available comment data
  * run flake8 on travis and ask contributors to do so
  * flake8 fixes in bugsy package

0.4.1 / 2014-05-26
==================

 * remove unused imports
 * If we get an error when searching throw a search exception and pass through the error from Bugzilla
 * add text property to Comment class
 * add id property to Comment class
 * Make contributing docs more thorough around creating a virtualenv and testing
 * Allow authenticating to Bugzilla with a userid and cookie.
 * When updating a bug that already exists we should use PUT not POST

0.4.0 / 2014-12-05
==================

 * Add in the ability to use change history fields for searchings
 * allow searching to handle time frames
 * Change UserAgent for bugsy to that Bugzilla knows that it is us calling. Fixes #4
 * Add version added to comments documentation
 * Add documenation for comments

0.3.0 / 2014-07-14
==================

 * Updated Documentation
 * Fix adding comments to bugs that already exist. Fixes #2
 * Give the ability to search for multiple bugs which allows changing the fields returned
 * Only request a small number of fields from Bugzilla. Fixes #3
 * Initial Comments API design

0.2.0 / 2014-06-26
==================

 * Added the ability to search Bugzilla
    * Set include_fields to have defaults as used in Bugs object
    * Add the ability to search whiteboard
    * Add the ability to search summary fields
    * Add in the ability to search for bugs assigned to people

0.1.0
==============================

 * Initial implementation
