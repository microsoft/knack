CLI
===

CLI provides the entry point.

The CLI object is used as a context, `ctx`, that is passed around throughout the application. You will see this context, `ctx`, referenced frequently.

We recommend specifying `cli_name`, `config_dir` and `config_env_var_prefix`.

For example:  
`cli_name` - Name of CLI. Typically the executable name.  
`config_dir` - Path to config dir. e.g. `os.path.join('~', '.myconfig')`  
`config_env_var_prefix` - A prefix for environment variables used in config e.g. `CLI_`.

Use the `invoke()` method to invoke commands.

For example:

```Python
mycli = CLI(commands_loader_cls=MyCommandsLoader)
exit_code = mycli.invoke(sys.argv[1:])
```


How do I?
---------

### Show my own version info ###

Subclass `CLI` and override `get_cli_version()`.
