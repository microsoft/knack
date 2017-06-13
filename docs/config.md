Config
======

The config system is used for user-configurable options.  
They are backed by environment variables and config files.

Here are the layers of config, with each layer overriding the layer below it:

| Config hierarchy      |
|-----------------------|
| Command line argument |
| Environment variable  |
| Config file           |

Use the `config_dir` and `config_env_var_prefix` options in the constructor of `CLI` to set the config directory and environment variable prefix.

Here's an example:

Let's assume `config_dir=~/.myconfig` and `config_env_var_prefix='CLI'`.

Environment variable format `export PREFIX_SECTION_OPTION=value`.

Config file format:
```
[section]
option = value
```

So to set the output type of commands, a user can set the environment variable CLI_CORE_OUTPUT or specify the section and option in the config file.  
The environment variable will override the config file.  
Lastly, some configurations (like output type) can be specified on a command-by-command basis also.
