==========================================
Pyramid Application Description Generation
==========================================

.. warning::

  2013/09/10: this package is brand new and not ready to be used. Come
  back in a couple of weeks.

.. important::

  Although pyramid-describe is intended to be able to describe any
  kind of pyramid dispatch approach, currently it only supports
  pyramid-controllers_ based hierarchies.

A pyramid plugin that describes a pyramid application URL hierarchy,
either by responding to an HTTP request or on the command line, via
application inspection and reflection.

Exposing an application's structure via HTTP is useful to dynamically
generate an API description (via WADL, JSON, or YAML) or to create
documentation directly from source code.

On the command-line it is useful to get visibility into an
application's URL structure and hierarchy so that it can be understood
and maintained.


TL;DR
=====

Install:

.. code-block:: bash

  $ pip install pyramid-describe

On the command-line:

.. code-block:: bash

  $ pdescribe config.ini --tree
  /
  ├── contact/
  │   ├── add
  │   ├── delete
  │   ├── list
  │   └── update
  ├── login
  └── logout


Configuration
=============

* describe.prefixes : list(str), default: 'describe'
* describe.name : str, default: application
* describe.attach : str, default: /describe
  ==> /describe/{describe.name}.{EXT}
* describe.url : str, default: /
* describe.include : list(str), default: None
* describe.exclude : list(str), default: None
* describe.parser : resolve-spec, default: pyramid_describe.parser.Parser
* describe.parser.{OPTION}
* describe.filter : resolve-spec, default: None
* describe.filter.{OPTION}
* describe.formats : list(str), default: ['html', 'txt', 'rst', 'json', 'yaml', 'wadl', 'xml']
* describe.format.default : str, default: `describe.formats`[0]
* describe.format.default.{OPTION}
* describe.format.override.{OPTION}
* describe.format.{FORMAT}.default.{OPTION}
* describe.format.{FORMAT}.override.{OPTION}
*    .restVerbs : list(str), default: pyramid_controllers.restcontroller.HTTP_METHODS
* describe.format.{FORMAT}.renderer : asset-spec, default: pyramid_describe:template/{FORMAT}.mako


.. _pyramid-controllers: https://pypi.python.org/pypi/pyramid_controllers
