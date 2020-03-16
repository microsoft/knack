Logging
=======

| Log Level   |  Usage                                                                                      |
|-------------|---------------------------------------------------------------------------------------------|
| Critical    | A serious error, program may be unable to continue running.                                 |
| Error       | Serious problem, software has not been able to perform some function.                       |
| Warning     | Something you want to draw the attention of the user to. Software still working as expected |
| Info        | Confirmation that things are working as expected.                                           |
| Debug       | Detailed information, useful for diagnostics.                                               |

- By default, log messages Warning and above are shown to the user.
- `--verbose` - This flag changes the logging level to Info and above.
- `--debug` - This flag changes the logging level to Debug and above.
- `--only-show-errors` - This flag changes the logging level to Error only, suppressing Warning.

* All log messages go to STDERR (not STDOUT)
* Log to Error or Warning for user messages instead of using the `print()` function
* If file logging has been enabled by the user, full Debug logs are saved to rotating log files.
    * File logging is enabled if section=logging, option=enable_log_file is set in config (see [config](config.md)).


Get the logger
--------------

```Python
from knack.log import get_logger
logger = get_logger(__name__)
```

See [Python Logger documentation](https://docs.python.org/3/library/logging.html#logging.Logger.debug) for how to format log messages.
