Validators
==========

Validators allow you to validate or transform command arguments just before execution.

Knack supports both command-level and argument-level validators.

If a command has a command-level validator, then any argument-level validators that would ordinarily be applied are ignored.

i.e. A command can have at most command validator or many argument level validators.

**Command-level Validators**
Command-level validators can operate on any arguments on the command. This is useful when you want a validator to make use of more than a single argument.

**Argument-level Validators**
Argument-level validators should only operate on a single argument.

The order argument-level validators are executed in is not guaranteed so don't use an arguments that make use of multiple arguments.

