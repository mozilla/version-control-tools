  $ . $TESTDIR/hgext/configwizard/tests/helpers.sh

Rejecting format-source doesn't enable it

  $ hg --config ui.interactive=true --config configwizard.steps=format-source,configchange configwizard << EOF
  > 
  > n
  > EOF
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>
  The "format-source" extension provides a way to run code-formatting tools in a way that
  avoids conflicts related to this formatting when merging/rebasing code across the
  reformatting.
  An example of a .hgrc configuration that uses our embedded clang-format and prettier-format
  utilities from 'mach' is as follows:
  [format-source]
  clang-format = [Path To Mozilla Repo]/mach clang-format --assume-filename $HG_FILENAME -p
  clang-format:configpaths = .clang-format, .clang-format-ignore
  clang-format:fileext = .cpp, .c, .h
  prettier-format = [Path To Mozilla Repo]/mach prettier-format --assume-filename $HG_FILENAME -p
  prettier-format:configpaths = .prettierrc, .prettierignore
  prettier-format:fileext = .js, .jsx, .jsm
  
  If `clang-format` or `prettier-format` are not present under `[format-source]`, a default
  configuration will be used that is embedded in this extension. The default configuration
  can be used in most cases.
  Would you like to activate format-source (Yn)?  n
No prompt if extensions already enabled

  $ hg --config configwizard.steps=format-source --config extensions.format-source=$TESTDIR/hgext/format-source configwizard
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>



format-source enabled when requested

  $ hg --config configwizard.steps=format-source,configchange configwizard
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>
  The "format-source" extension provides a way to run code-formatting tools in a way that
  avoids conflicts related to this formatting when merging/rebasing code across the
  reformatting.
  An example of a .hgrc configuration that uses our embedded clang-format and prettier-format
  utilities from 'mach' is as follows:
  [format-source]
  clang-format = [Path To Mozilla Repo]/mach clang-format --assume-filename $HG_FILENAME -p
  clang-format:configpaths = .clang-format, .clang-format-ignore
  clang-format:fileext = .cpp, .c, .h
  prettier-format = [Path To Mozilla Repo]/mach prettier-format --assume-filename $HG_FILENAME -p
  prettier-format:configpaths = .prettierrc, .prettierignore
  prettier-format:fileext = .js, .jsx, .jsm
  
  If `clang-format` or `prettier-format` are not present under `[format-source]`, a default
  configuration will be used that is embedded in this extension. The default configuration
  can be used in most cases.
  Would you like to activate format-source (Yn)?  y
  Your config file needs updating.
  Would you like to see a diff of the changes first (Yn)?  y
  --- hgrc.old
  +++ hgrc.new
  @@ -0,0 +1,2 @@
  +[extensions]
  +format-source = */hgext/format-source (glob)
  
  Write changes to hgrc file (Yn)?  y






  $ cat .hgrc
  [extensions]
  format-source = */hgext/format-source (glob)
