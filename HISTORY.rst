.. :changelog:

Release History
===============

unreleased
^^^^^^^^^^

* Support command level and argument level validators.
* knack.commands.CLICommandsLoader no accepts a `command_cls` argument so you can provide your own `CLICommand` class.
* logging: make determine_verbose_level private method.
* Allow overriding of NAMED_ARGUMENTS
* Only pass valid argparse kwargs to argparse.ArgumentParser.add_argument and ignore the rest

0.1.1 (2017-07-05)
^^^^^^^^^^^^^^^^^^

* Add more types of command and argument loaders.
* Add tests.

0.1.0 (2017-06-16)
^^^^^^^^^^^^^^^^^^

* Initial release
