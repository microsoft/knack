Arguments
=========

Arguments are stored in the `CLICommandsLoader` as an `ArgumentRegistry`.

**Customizing Arguments**

There are a number of customizations that you can make to the arguments of a command that alter their behavior within the CLI. To modify/enhance your command arguments, use `ArgumentsContext`.

- `dest` - This string is the name of the parameter you wish to modify, as specified in the function signature.
- `scope` - This string is the level at which your customizations are applied. For example, consider the case where you have commands `mycli mypackage command1` and `mycli mypackage command2`, which both have a parameter `my_param`.

```Python
with ArgumentsContext(self, 'mypackage') as ac:
    ac.argument('my_param', ...)  # applies to both command1 and command2
```
But
```Python
with ArgumentsContext(self, 'mypackage command1') as ac:
    ac.argument('my_param', ...)  # applies to command1 but not command2
```
Like CSS rules, modifications are applied in order from generic to specific.
```Python
with ArgumentsContext(self, 'mypackage') as ac:
    ac.argument('my_param', ...)  # applies to both command1 and command2
with ArgumentsContext(self, 'mypackage command1') as ac:
    ac.argument('my_param', ...)  # applies to command1 but not command2  # command2 inherits and build upon the previous changes
```

- `arg_type` - An instance of the `CLIArgumentType` class. This essentially serves as a named, reusable packaging of the `kwargs` that modify your command's argument. It is useful when you want to reuse an argument definition, but is generally not required. It is most commonly used for name type parameters.
- `kwargs` - Most likely, you will simply specify keyword arguments in `ArgumentsContext.argument` that will accomplish what you need.  Any `kwargs` specified will override or extended the definition in `arg_type`, if provided.

The follow keyword arguments are supported:
- `options_list` - By default, your argument will be exposed as an option in hyphenated form (ex: `my_param` becomes `--my-param`). If you would like to change the option string without changing the parameter name, and/or add a short option, specify the `options_list` kwarg. This is a tuple of two string values, one for an standard option string, and the other for an optional short string. (Ex: `options_list=('--myparam', '-m')`)
- `validator` - The name of a callable that takes the function namespace as a parameter. Allows you to perform any custom logic or validation on the entire namespace prior to command execution. Validators are executed after argument parsing, and thus after `type` and `action` have been applied. However, because the order in which validators are exectued is random, you should not have multiple validators modifying the same parameter within the namespace.
- `completer` - The name of a callable that takes the following parameters `(prefix, action, parsed_args, **kwargs)` and return a list of completion values.

Additionally, the following `kwargs`, supported by argparse, are supported as well:
- `nargs` - See https://docs.python.org/3/library/argparse.html#nargs
- `action` - See https://docs.python.org/3/library/argparse.html#action
- `const` - See https://docs.python.org/3/library/argparse.html#const
- `default` - See https://docs.python.org/3/library/argparse.html#default. Note that the default value is inferred from the parameter's default value in the function signature. If specified, this will override that value.
- `type` - See https://docs.python.org/3/library/argparse.html#type
- `choices` - See https://docs.python.org/3/library/argparse.html#choices. If specified this will also serve as a value completer for people using tab completion.
- `required` - See https://docs.python.org/3/library/argparse.html#required. Note that this value is inferred from the function signature depending on whether or not the parameter has a default value. If specified, this will override that value.
- `help` - See https://docs.python.org/3/library/argparse.html#help. Generally you should avoid adding help text in this way, instead opting to create a help file as described above.
- `metavar` - See https://docs.python.org/3/library/argparse.html#metavar
