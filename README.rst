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
  / (root)
  ├── static/*
  ├── login
  ├── logout
  └── contact/
      ├── add
      ├── delete
      ├── list
      └── update


Configuration
=============

* describe.url
* describe.target
* describe.parser
* describe.renderer


.. _pyramid-controllers: https://pypi.python.org/pypi/pyramid_controllers
