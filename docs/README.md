Documentation
=============

CLI Patterns
------------

- Be consistent with POSIX tools.
- CLI success comes from ease and predictability of use so be consistent.
- Support Piping and output direction to chain commands together.
- Work with GREP, AWK, JQ and other common tools and commands.
- Support productivity features like tab completion and parameter value completion.

* Commands should follow a "[noun] [noun] [verb]" pattern.
    * *For nouns that only support a single verb, the command should be named as a single hyphenated verb-noun pair.*
* Commands should support all output types (be consistent).
    * *Exceptions are okay if only a 'raw' format makes sense e.g. XML.*
* Commands and arguments should have descriptions.
    * *Include examples for the less straightforward commands.*
* Commands should return an object or dictionary, not strings/bools/etc.; `logging.info(“Upload of myfile.txt successful”)` **NOT** ~~`return “Upload successful”`~~.

- Log to ERROR or WARNING for user messages; don't use `print()` function (by default it goes to STDOUT).
- STDOUT vs. STDERR: STDOUT is used for actual command output. Everything else to STDERR (e.g. log/status/error messages).



Overall Architecture
--------------------

TODO Overall architecture of CLI, Invocations, etc.


Doc Sections
------------

- [Events](events.md) - Provides an extensible eventing module that you can hook into

- [Config](config.md) - Provides user-configurable options back by environment variables or config files

- [Logging](logging.md) - Provides consistent logging

- [Completion](completion.md) - Provides tab completion support

- [Prompting](prompting.md) - Provides a consistent user-prompting experience

- [Help](help.md) - Provides command/argument help

- [Output](output.md) - Provides output options and displays command output

- [Query](query.md) - Provides JMESPath query support

- [Testing](testing.md) - Provides a framework to test your commands
