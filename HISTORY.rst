.. :changelog:

Release History
===============

0.7.0rc1
+++++
* Allow disabling color (#171)
* Support yaml and yamlc output (#173)
* Drop support for python 2 and 3.5 (#174)
* Support ``--only-show-errors`` to disable warnings (#179)
* Add experimental tag (#180)

0.6.3
+++++
* Fix bug where arguments in preview did not call registered actions. This meant that parameter parsing did not behave
  completely as expected.

0.6.2
+++++
* Adds ability to declare that command groups, commands, and arguments are in a preview status and therefore might change or be removed. This is done by passing the kwarg `is_preview=True`.
* Adds a generic ``StatusTag`` class to ``knack.util`` that allows you to create your own colorized tags like ``[Preview]`` and ``[Deprecated]``.
* When an incorrect command name is entered, Knack will now attempt to suggest the closest alternative.

0.6.1
+++++
* Always read from local for configured_default

0.6.0
+++++
* Support local context chained config file

0.5.4
+++++
* Allows the loading of text files using @filename syntax.
* Adds the argument kwarg configured_default to support setting argument defaults via the config file's [defaults] section or an environment variable.

0.5.3
+++++
* Removes an incorrect check when adding arguments.

0.5.2
+++++
* Updates usages of yaml.load to use yaml.safe_load.

0.5.1
+++++
* Fix issue with some scenarios (no args and --version)

0.5.0
+++++
* Adds support for positional arguments with the .positional helper method on ArgumentsContext.
* Removes the necessity for the type field in help.py. This information can be inferred from the class, so specifying it causes unnecessary crashes.
* Adds support for examining the result of a command after a call to invoke. The raw object, error (if any) an exit code are accessible.
* Adds support for accessing the command instance from inside custom commands by putting the special argument cmd in the signature.
* Fixes an issue with the default config directory. It use to be .cli and is now based on the CLI name.
* Fixes regression in knack 0.4.5 in behavior when cli_name --verbose/debug is used. Displays the welcome message as intended.
* Adds ability to specify line width for help text display.

0.4.5
+++++
* Preserves logging verbosity and output format on the namespace for use by validators.

0.4.4
+++++
* Adds ability to set config file name.
* Fixes bug with argument deprecations.

0.4.3
+++++
* Fixes issue where values were sometimes ignored when using deprecated options regardless of which option was given.

0.4.2
+++++
* Bug fix: disable number parse on table mode PR #88

0.4.1
+++++
* Fixes bug with deprecation mechanism.
* Fixes an issue where the command group table would only be filled by calls to create CommandGroup classes. This resulted in some gaps in the command group table.

0.4.0
+++++
* Add mechanism to deprecate commands, command groups, arguments and argument options.
* Improve help display support for Unicode.

0.3.3
+++++
* expose a callback to let client side perform extra logics (#80)
* output: don't skip false value on auto-tabulating (#83)

0.3.2
+++++
* ArgumentsContext.ignore() should use hidden options_list (#76)
* Consolidate exception handling (#66)

0.3.1
+++++
* Performance optimization - Delay import of platform and colorama (#47)
* CLIError: Inherit from Exception directly (#65)
* Explicitly state which packages to include (so exclude 'tests') (#68)

0.2.0
+++++
* Support command level and argument level validators.
* knack.commands.CLICommandsLoader now accepts a command_cls argument so you can provide your own CLICommand class.
* logging: make determine_verbose_level private method.
* Allow overriding of NAMED_ARGUMENTS
* Only pass valid argparse kwargs to argparse.ArgumentParser.add_argument and ignore the rest
* logging: make determine_verbose_level private method
* Remove cli_command, register_cli_argument, register_extra_cli_argument as ways to register commands and arguments.

0.1.1
+++++
* Add more types of command and argument loaders.

0.1.0
+++++
* Initial release
