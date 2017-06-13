CLI
===

CLI provides the entry point.

We recommend specifying `cli_name`, `config_dir` and `config_env_var_prefix`.

For example:  
`cli_name` - Name of CLI. Typically the executable name.  
`config_dir` - Path to config dir. e.g. `os.path.join('~', '.myconfig')`  
`config_env_var_prefix` - A prefix for environment variables used in config e.g. `CLI_`.

How to
------

### Show my version info ###

Subclass `CLI` and override `get_cli_version()`.
