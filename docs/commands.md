Commands
========

The commands loader contains a command table.  
A command table is a dictionary from command name to a `CLICommand` instance.

**Writing a Command**

Write your command as a simple function, specifying your arguments as the parameter names.

When choosing names, it is recommended that you look at similiar commands and follow those naming conventions to take advantage of any aliasing that may already be in place.

If you specify a default value in your function signature, this will flag the argument as optional and will automatically display the default value in the help text for the command. Any parameters that do not have a default value are required and will automatically appear in help with the [Required] label. The required and default behaviors for arguments can be overridden if needed with the `register_cli_argument` function but this is not generally needed.

There are a few different ways to register commands (see the examples directory for working samples).  
Typically, you would use `CommandSuperGroup` and `CommandGroup` to register commands.

For example:

```Python
def hello_command_handler():
    return ['hello', 'world']

class MyCommandsLoader(CLICommandsLoader):

    def load_command_table(self, args):
        with CommandSuperGroup(__name__, self, '__main__#{}') as sg:
            with sg.group('hello') as g:
                g.command('world', 'hello_command_handler')
        return OrderedDict(self.command_table)

mycli = CLI(cli_name='mycli', commands_loader_cls=MyCommandsLoader)
exit_code = mycli.invoke(sys.argv[1:])
```

You can also provide your own command class to the CLICommandsLoader like so:

```Python
class MyCommandsLoader(CLICommandsLoader):

    def __init__(self, cli_ctx=None):
        super(MyCommandsLoader, self).__init__(cli_ctx=cli_ctx, command_cls=MyCustomCLICommand)

```
