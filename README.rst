===================================
Self-Documentation for Pyramid Apps
===================================

.. warning::

  2013/09/13: though functional, this package is pretty new... Come
  back in a couple of weeks if you don't like living on the
  alpha-edge!

A pyramid plugin that describes a pyramid application URL hierarchy,
either by responding to an HTTP request or on the command line, via
application inspection and reflection. It has built-in support for
plain-text hierachies, reStructuredText, HTML, JSON, YAML, WADL, and
XML, however other custom formats can be added easily.

Exposing an application's structure via HTTP is useful to dynamically
generate an API description (via WADL, JSON, or YAML) or to create
documentation directly from source code.

On the command-line it is useful to get visibility into an
application's URL structure and hierarchy so that it can be understood
and maintained.

.. note::

  Although pyramid-describe is intended to be able to describe any
  kind of pyramid application, currently it only supports
  pyramid-controllers_ based dispatch.


TL;DR
=====

Install:

.. code-block:: bash

  $ pip install pyramid-describe

Command-line example:

.. code-block:: bash

  $ pdescribe example.ini --format txt
  /                       # The application root.
  ├── contact/            # Contact manager.
  │   ├── <POST>          # Creates a new 'contact' object.
  │   └── {CONTACTID}     # RESTful access to a specific contact.
  │       ├── <DELETE>    # Delete this contact.
  │       ├── <GET>       # Get this contact's details.
  │       └── <PUT>       # Update this contact's details.
  ├── login               # Authenticate against the server.
  └── logout              # Remove authentication tokens.

Examples of the above application in all other formats with built-in
support are available at:
`text (pure-ASCII) <https://raw.github.com/cadithealth/pyramid_describe/master/doc/example.txt.asc>`_,
`reStructuredText <https://raw.github.com/cadithealth/pyramid_describe/master/doc/example.rst>`_,
`HTML <http://htmlpreview.github.io/?https://raw.github.com/cadithealth/pyramid_describe/master/doc/example.html>`_,
`JSON <https://raw.github.com/cadithealth/pyramid_describe/master/doc/example.json>`_,
`YAML <https://raw.github.com/cadithealth/pyramid_describe/master/doc/example.yaml>`_,
`WADL <https://raw.github.com/cadithealth/pyramid_describe/master/doc/example.wadl>`_,
and `XML <https://raw.github.com/cadithealth/pyramid_describe/master/doc/example.xml>`_.


Configuration
=============

* describe.prefixes : list(str), default: 'describe'
* describe.name : str, default: application
* describe.attach : str, default: /describe
  ==> /describe/{describe.name}.{EXT}
* describe.url : str, default: /
* describe.include : list(str), default: None
* describe.exclude : list(str), default: None
* describe.filters : list(resolve-spec), default: None
* describe.formats : list(str), default: ['html', 'txt', 'rst', 'json', 'yaml', 'wadl', 'xml']
* describe.format.default : str, default: `describe.formats`[0]
* describe.format.default.{OPTION}
* describe.format.override.{OPTION}
* describe.format.{FORMAT}.default.{OPTION}
* describe.format.{FORMAT}.override.{OPTION}
*    .restVerbs : list(str), default: pyramid_controllers.restcontroller.HTTP_METHODS
* describe.format.{FORMAT}.renderer : asset-spec, default: pyramid_describe:template/{FORMAT}.mako


.. _pyramid-controllers: https://pypi.python.org/pypi/pyramid_controllers
