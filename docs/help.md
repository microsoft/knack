# Help #

Help authoring for commands is done in a number of places. The YAML-based system is the recommended way to update command and group help text.

Command help starts with the docstring text on the handler, if available. Code can specify values that replace the docstring contents. YAML is the final override for help content and is the recommended way for authoring command and group help. Note that group help can only be authored via YAML.

Here are the layers of help, with each layer overriding the layer below it:

| Help Display   |
|----------------|
| YAML Authoring |
| Code Specified |
| Docstring      |


The YAML syntax is described [here](http://www.yaml.org/spec/1.2/spec.html "here").

Authoring note: it is not recommended to use the product code to author command/group help--YAML is the recommended way (see above). This information is provided for completeness and may be useful for fixing small typos in existing help text.

### Example YAML help ###

This is example YAML help for the command `mycli hello world`.

<pre>
from knack.help_files import helps

helps['hello world'] = """
            type: command
            short-summary: Say hello to the world.
            long-summary: Longer summary of saying hello.
            parameters:
                - name: --language -l
                  type: string
                  short-summary: 'Language to say hello in'
                  long-summary: |
                      Longer summary with newlines preserved. Preserving newlines is helpful for paragraph breaks.
                  populator-commands:
                  - mycli hello languages
                  - These indicate where values can be retrieved for input to this command
                - name: --another-parameter
                  short-summary: These parameter names must match what is shown in the command's CLI help output, including abbreviation.
            examples:
                - name: Document a parameter that doesn't exist
                  text: >
                    You will get an error when you show help for the command stating there is an extra parameter.
                - name: Collapse whitespace in YAML
                  text: >
                    The > character collapses multiple lines into a single line, which is good for on-screen wrapping.
            """
</pre>

You can also document groups using the same format.

<pre>
helps['hello'] = """
            type: group
            short-summary: Commands to say hello
            long-summary: Longer summary of the hello group
            examples:
                - name: Example name
                  text: Description
            """
</pre>

# Tips to write effective help for your command

- Make sure the doc contains all the details that someone unfamiliar with the API needs to use the command.
- Examples are worth a thousand words. Provide examples that cover common use cases.
- Don't use "etc". Sometimes it makes sense to spell out a list completely. Sometimes it works to say "like ..." instead of "..., etc".
- The short summary for a group should start with "Commands to...".
- Use active voice. For example, say "Update web app configurations" instead of "Updates web app configurations" or "Updating web app configurations".
- Don't use highly formal language. If you imagine that another dev sat down with you and you were telling him what he needs to know to use the command, that's exactly what you need to write, in those words.

# Testing Authored Help #

To verify the YAML help is correctly formatted, the command/group's help command must be executed at runtime. For example, to verify `mycli hello world`, run the command `mycli hello world -h` and verify the text.

Runtime is also when help authoring errors will be reported, such as documenting a parameter that doesn't exist. Errors will only show when the CLI help is executed, so verifying the CLI help is required to ensure your authoring is correct.
