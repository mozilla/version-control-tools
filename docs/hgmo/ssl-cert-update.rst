Updating the Hg Certificate
===========================

Every two years, the Hg SSL Certificate expires and must be renewed.  This requires actions
by several parties: Mozilla Hg Developers, WebOps and end users.  It is assumed that the Mozilla Hg
Developers will orchestrate the certificate rollover by following these steps:

1. About one month out from expiration:

 * File tracking bug for Certificate Update
 * File bug for WebOps to:

  - Generate new certificate
  - Install in load balancer **without enabling it**
  - Take note of the new SHA256 fingerprint for future reference

2. One week before the new certificate goes live:

 * Send notifications to users of their need to act

  - See text of “Sample Announcement to Users” below
  - Announce timing of new certificate activation
  - Include new certificate fingerprint

   + This information can be sent directly or as a reference to a bug comment, as was done in 2018.
   + See “Sample Additional Instructions For Users” below

  - Places for the announcements:

   + <dev-version-control@lists.mozilla.org>
   + <release-engineering@lists.mozilla.org>
   + <dev-platform@lists.mozilla.org>

  - In 2018, announcements were also made to these lists, but the actual list addresses were obfuscated and their actual names unknown. *Please update this document if anyone knows the identity of these mailing lists*

   + <firef...@mozilla.org>
   + <firef...@mozilla.com>
   + <auto-...@mozilla.com>

3. At transition time:

 * File bug to update server side certificate fingerprint

  - Configwizard extension
  - Taskcluster secret ``project/taskcluster/gecko/hgfingerprint``

 * Get WebOps to activate the certificate
 * Deploy server side certificate changes

4. Ensure everything works

 * Immediately after the new certificate is live, and local ``hostsecurity`` has been set, try a ``hg clone`` or ``hg pull`` to ensure that Hg is working with the new certificate.



Sample Preliminary Announcement to Users:
-----------------------------------------
Each biennium, the users need to be notified of actions they need to take at the
time of the certificate roll over. The following are edited quotes of the 2018 messages
to users. The details change, so a literal use of these quotes may not be
appropriate.

In the quote below, datetimes, bug numbers, and SHA fingerprints have been replaced
with substitution variables of the form `{VARIABLE_NAME}`. If using this quote
to make a new message, take care to replace the substitution variables appropriately.

  hg.mozilla.org's x509 server certificate (AKA an "SSL certificate") will
  be rotated at {DATETIME} Bug {TRACKING_BUG_NUMBER} tracks this change.

  You may have the certificate's fingerprint pinned in your hgrc files.
  Automated jobs may pin the fingerprint as well. *If you have the
  fingerprint pinned, you will need to take action otherwise Mercurial will
  refuse the connect to hg.mozilla.org once the certificate is swapped.*

  The easiest way to ensure your pinned fingerprint is up-to-date is to run
  ``mach vcs-setup`` from a Mercurial checkout (it can be from an old
  revision). If running Mercurial 3.9+ (which you should be in order to have
  security fixes), both the old and new fingerprints will be pinned and the
  transition will "just work." Once the new fingerprint is enabled on the server,
  run ``mach vcs-setup`` again to remove the old fingerprint.

  Fingerprints and details of the new certificate (including hgrc config
  snippets you can copy) are located at Bug {CERT_BUG_NUMBER} From a
  certificate level, this transition is pretty boring: just a standard
  certificate renewal from the same CA.

  The Matric channel for this operational change will be #vcs. Fallout in
  Firefox CI should be discussed in #ci. Please track any bugs related to
  this change against Bug {TRACKING_BUG_NUMBER}.


Sample Additional Instructions for users:
-----------------------------------------

  The new certificate has been issued in bug {BUG_NUMBER}.

  The new fingerprint:

  sha256: {SHA256_FINGERPRINT}

  We plan to swap in the new certificate on {DATETIME}.


  Mercurial's fingerprint pinning should be configured as follows:
  Be careful of whitespace when copying the fingerprints. They should be in a comma-delimited list
  on the same line in the file:

  **Mercurial 3.9+**

  [hostsecurity]
  hg.mozilla.org:fingerprints = sha256:{OLD_SHA256_FINGERPRINT},sha256:{SHA256_FINGERPRINT}


  *After the new certificate is live*

  After the new certificate is installed, you can drop the old certificate fingerprint from the config.

  **Mercurial 3.9+**

  [hostsecurity]
  hg.mozilla.org:fingerprints = sha256:{SHA256_FINGERPRINT}
