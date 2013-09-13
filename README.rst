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

When pyramid-describe is integrated via inclusion
(e.g. ``config.include('pyramid_describe')``), the module will
auto-create DescribeController's as defined in the application's
settings. The following configurations can be specified there (note
that the first one controls the prefix set on the others):

* ``describe.prefixes`` : list(str), default: 'describe'

  Defines the prefix or the list of prefixes that pyramid-describe
  settings will be searched for in the configuration. For each prefix,
  a separate DescribeController will be created and attached to the
  application router. The following example attaches two controllers
  at ``/desc-one`` and ``/desc-two``:

  .. code-block:: ini

    [app:main]
    describe.prefixes = describe-one describe-two
    describe-one.attach  = /desc-one
    # other `describe-one` options...
    describe-two.attach  = /desc-two
    # other `describe-two` options...

* ``{PREFIX}.attach`` : str, default: /describe

  Specifies the path to attach the controller to the current
  application's router. Note that this uses the `add_controller`
  directive, and ensures that pyramid-controllers has already been
  added via an explicit call to ``config.include()``. This path will
  serve the default format: to request alternate formats, use
  "PATH/FILENAME.EXT" (where FILENAME is controlled by the
  ``{PREFIX}.filename`` configuration and EXT specifies the format)
  or use the "format=EXT" query-string. Examples using the default
  settings:

  .. code-block:: text

    http://localhost:8080/describe/application.txt
    http://localhost:8080/describe/application.json
    http://localhost:8080/describe?format=json

* ``{PREFIX}.filename`` : str, default: application

  Sets the filename base component. Typically, this is set to the
  application's name and should probably include the application
  version.

* ``{PREFIX}.redirect`` : str, default: None

  Similar to the `filename` option, this option sets a filename base
  component that will redirect (with a 302) to the current `filename`.
  This allows there to be a persistent known location that can be used
  if the `filename` option is dynamic or changes with revisions.

* ``{PREFIX}.inspect`` : str, default: /

  Specifies the top-level URL to start the application inspection at.

* ``{PREFIX}.include`` : list(str), default: None

  The `include` option lists regular expressions that an endpoint must
  match at least one of in order to be included in the output.  This
  option can be used with the `exclude` option, in which case
  endpoints are first matched for inclusion, then matched for
  exclusion (i.e. the order is "allow,deny" in apache terminology).

* ``{PREFIX}.exclude`` : list(str), default: None

  The converse of the `include` option.


.. _pyramid-controllers: https://pypi.python.org/pypi/pyramid_controllers
