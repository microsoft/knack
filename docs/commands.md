Commands
========

The commands loader contains a command table.
A command table is a dictionary from command name to a `CLICommand` instance.

**Writing a Command**

Write your command as a simple function, specifying your arguments as the parameter names.

When choosing names, it is recommended that you look at similar commands and follow those naming conventions to take advantage of any aliasing that may already be in place.

If you specify a default value in your function signature, this will flag the argument as optional and will automatically display the default value in the help text for the command. Any parameters that do not have a default value are required and will automatically appear in help with the [Required] label. The required and default behaviors for arguments can be overridden if needed with the `ArgumentsContext` function but this is not generally needed.

There are a few different ways to register commands (see the examples directory for working samples).
Typically, you would use `CommandGroup` to register commands.

For example:

```Python
def hello_command_handler():
    return ['hello', 'world']

class MyCommandsLoader(CLICommandsLoader):

    def load_command_table(self, args):
        with CommandGroup(__name__, self, 'hello', '__main__#{}') as g:
            g.command('world', 'hello_command_handler')
        return OrderedDict(self.command_table)

mycli = CLI(cli_name='mycli', commands_loader_cls=MyCommandsLoader)
exit_code = mycli.invoke(sys.argv[1:])
```

You can specify `arguments_loader` and `description_loader` functions on a
`CommandGroup` or an individual command. Command-level values override group
values. An omitted command-level hook inherits the group value, if any; an absent
hook after inheritance or an explicit command-level `None` selects the lazy
handler-signature default. The argument hook returns `(name, CLICommandArgument)`
pairs and the description hook returns the description text. Group-level hooks
are defaults for each registered command, not a replacement for YAML group help.
After loading arguments, `CLICommandsLoader.load_arguments` still applies
registered `ArgumentsContext` overrides and extra arguments.

Default selection does not truth-test a supplied hook. A custom command class
receives a non-`None` value unchanged from `create_command`; group defaults are
first deep-copied by `CommandGroup.command`. The stock `CLICommand` still
truth-tests hooks before using them, so falsey callable objects are not executed
by that class. Non-callable values such as `False` are not supported hooks or
documented sentinels for disabling inference; use a function returning an empty
argument list when that is intended.

You can also provide your own command class to the CLICommandsLoader like so:

```Python
class MyCommandsLoader(CLICommandsLoader):

    def __init__(self, cli_ctx=None):
        super(MyCommandsLoader, self).__init__(cli_ctx=cli_ctx, command_cls=MyCustomCLICommand)
```
