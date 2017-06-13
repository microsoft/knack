# Completion #

Tab completion is provided by [argcomplete](http://pypi.python.org/pypi/argcomplete).

In your environment, you can enable it with `eval "$(register-python-argcomplete CLI_NAME)"`.

You will then get tab completion for all command names, command arguments and global arguments.

## How to ship tab completion support with your pip package ##

With the PyPI package of your CLI, you can include a shell script.

For example:  
`mycli.completion.sh`
```Bash
case $SHELL in
*/zsh)
   echo 'Enabling ZSH compatibility mode';
   autoload bashcompinit && bashcompinit
   ;;
*/bash)
   ;;
*)
esac

eval "$(register-python-argcomplete mycli)"
```

In your `setup.py` file, include this script so it is included in your package.

```Python
setup(
    scripts=['mycli.completion.sh', ...],
)
```

Once your CLI has been installed with `pip`, instruct your users to source your completion file.

```Bash
source mycli.completion.sh
```

## How to ship tab completion support with your other installers ##

The method above will not work for other installers as `register-python-argcomplete` is a command that gets enabled when `argcomplete` is installed with pip.

`register-python-argcomplete` is a command that produces a shell script that you can consume directly; you can see this with running `register-python-argcomplete --no-defaults mycli`.

We directly use the output of the above command.

`mycli.completion`
```Bash
_python_argcomplete() {
    local IFS=$'\013'
    local SUPPRESS_SPACE=0
    if compopt +o nospace 2> /dev/null; then
        SUPPRESS_SPACE=1
    fi
    COMPREPLY=( $(IFS="$IFS" \
                  COMP_LINE="$COMP_LINE" \
                  COMP_POINT="$COMP_POINT" \
                  COMP_TYPE="$COMP_TYPE" \
                  _ARGCOMPLETE_COMP_WORDBREAKS="$COMP_WORDBREAKS" \
                  _ARGCOMPLETE=1 \
                  _ARGCOMPLETE_SUPPRESS_SPACE=$SUPPRESS_SPACE \
                  "$1" 8>&1 9>&2 1>/dev/null 2>/dev/null) )
    if [[ $? != 0 ]]; then
        unset COMPREPLY
    elif [[ $SUPPRESS_SPACE == 1 ]] && [[ "$COMPREPLY" =~ [=/:]$ ]]; then
        compopt -o nospace
    fi
}
complete -o nospace -F _python_argcomplete "mycli"
```

Ship the above file and include it as part of each installer.
