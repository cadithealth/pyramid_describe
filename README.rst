==============================
Pyramid Application Inspection
==============================

.. warning::

  2013/09/09: this package is brand new and not ready to be used. Come
  back in a couple of weeks.

A pyramid plugin that inspects and renders a pyramid application URL hierarchy.

TL;DR
=====

Install:

.. code-block:: bash

  $ pip install pyramid-inspect

On the command-line:

.. code-block:: bash

  $ pinspect config.ini --tree
  / (root)
  ├── static/*
  ├── login
  ├── logout
  └── todo/
      ├── add
      ├── delete
      ├── list
      └── update
