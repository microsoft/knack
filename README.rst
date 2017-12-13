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


.. code-block:: bash

    pip install knack


.. note::  🚨  The project is in `initial development phase <https://semver.org/#how-should-i-deal-with-revisions-in-the-0yz-initial-development-phase>`__ . We recommend pinning to at least a specific minor version when marking **knack** as a dependency in your project.


Usage
=====


.. code-block:: python

    import sys
    from collections import OrderedDict
    from knack import CLI, CLICommandsLoader, ArgumentsContext

    def abc_list(myarg):
        import string
        return list(string.ascii_lowercase)

    class MyCommandsLoader(CLICommandsLoader):
        def load_command_table(self, args):
            with CommandGroup(__name__, self, 'abc', '__main__#{}') as g:
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

In a virtual environment, install the `requirements.txt` file.

.. code-block:: bash

    pip install -r requirements.txt
    pip install -e .

Run Automation
==============

This project supports running automation using `tox <https://tox.readthedocs.io/en/latest/>`__.

.. code-block:: bash

    pip install tox
    tox


Real-world uses
===============

- `VSTS CLI <https://github.com/Microsoft/vsts-cli>`__: A command-line interface for Visual Studio Team Services (VSTS) and Team Foundation Server (TFS). With the VSTS CLI, you can manage and work with resources including pull requests, work items, builds, and more.
- `Service Fabric CLI <https://github.com/Azure/service-fabric-cli>`__: A command-line interface for interacting with Azure Service Fabric clusters and their related entities.

Do you use knack in your CLI as well? Open a pull request to include it here. We would love to have it in our list.


Release History		
===============

See `GitHub Releases <https://github.com/Microsoft/knack/releases>`__.


Contribute Code
===============

This project has adopted the `Microsoft Open Source Code of Conduct <https://opensource.microsoft.com/codeofconduct/>`__.

For more information see the `Code of Conduct FAQ <https://opensource.microsoft.com/codeofconduct/faq/>`__ or contact `opencode@microsoft.com <mailto:opencode@microsoft.com>`__ with any additional questions or comments.

If you would like to become an active contributor to this project please
follow the instructions provided in `Contribution License Agreement <https://cla.microsoft.com/>`__


License
=======

Knack is licensed under `MIT <LICENSE>`__.

