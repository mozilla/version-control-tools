.. _cross_channel:

==================
Cross-channel L10n
==================

.. toctree::
   :maxdepth: 1

   architecture

.. note::

   This documentation is for code yet to be written. Its intention is to
   serve as a guideline for what could and probably should be, not as
   something that is.

Cross-channel Localization (aka x-channel L10n) allows us to create one
localization for all currently shipping versions of Firefox, Firefox for
Android, as well as Thunderbird and SeaMonkey.

At any point in time, in en-US we have anywhere between 8 and 10 versions
in two conceptual DAGs involved. To have one localization for all, we need
to provide the superset of all the strings on all those version in each
localization.

The way we do that is by creating a repository containing those English 
strings, and expose that to localization.

To write this out, say we had three upstream repositories,
:file:`mozilla-central`, :file:`releases/mozilla-beta`, and 
:file:`comm-central`. In comm-central, we have
:file:`mail/locales/en-US/mail.properties` with the following content

.. code-block:: properties

   send-mail = Send Mail

In mozilla-central, we have
:file:`browser/locales/en-US/browser.properties` with

.. code-block:: properties

  open-window = Open Window
  close-window = Close Window
  open-tab = Open Tab

and the corresponding file on the beta branch in releases/mozilla-beta
is

.. code-block:: properties

  open-window = Open Window
  open-new-window = Open New Window
  close-window = Close Window

The generated repository should have two files, which paths correspond to
those in the upstream repositories, but don't have the ``locales/en-US`` in
them. The contents of :file:`browser/browser.properties` are

.. code-block:: properties

  open-window = Open Window
  open-new-window = Open New Window
  close-window = Close Window
  open-tab = Open Tab

with the two shared strings from central and beta, and each of the two
unique strings from central and aurora, in a good order in the resulting file.
For comm-central, it also has :file:`mail/mail.properties`

.. code-block:: properties

   send-mail = Send Mail

For simplicity, we didn't create a diverging branch of this file in this
example, but it'd work exactly like in ``browser.properties``.

As part of the generation, we also rewrite the configuration files from the
upstream repository to be valid configuration files in the generated
repository.
