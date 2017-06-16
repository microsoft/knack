Knack
=====

.. image:: https://img.shields.io/pypi/v/knack.svg
    :target: https://pypi.python.org/pypi/knack

.. image:: https://img.shields.io/pypi/pyversions/knack.svg
    :target: https://pypi.python.org/pypi/knack

.. image:: https://travis-ci.org/Microsoft/knack.svg?branch=master
    :target: https://travis-ci.org/Microsoft/knack


------------

::

    _                     _    
   | | ___ __   __ _  ___| | __
   | |/ / '_ \ / _` |/ __| |/ /
   |   <| | | | (_| | (__|   < 
   |_|\_\_| |_|\__,_|\___|_|\_\


**A Command-Line Interface framework**

```
pip install knack
```


Usage
=====


.. code-block:: python

    from knack import CLI, CLICommandsLoader, CLICommand

    def abc_list(myarg):
        import string
        return list(string.ascii_lowercase)

    class MyCommandsLoader(CLICommandsLoader):
        def load_command_table(self, args):
            with CommandSuperGroup(__name__, self, '__main__#{}') as sg:
                with sg.group('abc') as g:
                    g.command('list', 'abc_list')
            return OrderedDict(self.command_table)

        def load_arguments(self, command):
            with ArgumentsContext(self, 'abc list') as ac:
                ac.argument('myarg', type=int, default=100)
            super(MyCommandsLoader, self).load_arguments(command)

    mycli = CLI(cli_name='mycli', commands_loader_cls=MyCommandsLoader)
    exit_code = mycli.invoke(sys.argv[1:])
    sys.exit(exit_code)


More samples and snippets available at `examples <examples>`__.


Documentation
=============

Documentation is available at `docs <docs>`__.

Developer Setup
===============

In a virtual environment, install the requirements.txt file.

.. code-block:: bash

    pip install -r requirements.txt
    pip install -e .


Contribute Code
===============

This project has adopted the `Microsoft Open Source Code of Conduct <https://opensource.microsoft.com/codeofconduct/>`__.

For more information see the `Code of Conduct FAQ <https://opensource.microsoft.com/codeofconduct/faq/>`__ or contact `opencode@microsoft.com <mailto:opencode@microsoft.com>`__ with any additional questions or comments.

If you would like to become an active contributor to this project please
follow the instructions provided in `Contribution License Agreement <https://cla.microsoft.com/>`__


License
=======

Knack is licensed under `MIT <LICENSE>`__.
