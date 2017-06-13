Output
======

In general, all commands produce an output object that can be converted to any of the available output types by the CLI core.

In other words, commands are output type independent.

Supported output types:
- JSON (human readable, can handle complex objects, useful for queries.
- JSON colored
- Table (human readable format)
- TSV (great for *nix scripting e.g. with awk, grep, etc.)

Table and TSV format can't display nested objects so a user can use the `--query` argument to select the properties they want to display.

The `table_transformer` is available when registering a command to define how it should look in table output.
