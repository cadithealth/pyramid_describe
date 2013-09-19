===================================
Self-Documentation for Pyramid Apps
===================================

.. warning::

  2013/09/13: though functional, this package is pretty new... Come
  back in a couple of weeks if you don't like living on the
  beta-edge!

A pyramid plugin that describes a pyramid application URL hierarchy,
either by responding to an HTTP request or on the command line, via
application inspection and reflection. It has built-in support for
plain-text hierachies, reStructuredText, HTML, PDF, JSON, YAML, WADL,
and XML, however other custom formats can be added easily.

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
`PDF <https://raw.github.com/cadithealth/pyramid_describe/master/doc/example.pdf>`_,
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

* ``describe.class`` : resolve-spec, default: pyramid_describe.DescribeController

  Sets the global default Controller class that will be instantiated
  for each of the stanzas defined in `describe.prefixes`. Note that
  this option can be overriden on a per-stanza basis.

* ``{PREFIX}.class`` : resolve-spec, default: `describe.class`

  Sets the Controller class that will be instantiated for this PREFIX
  stanza, overriding `describe.class`.

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

* ``{PREFIX}.redirect`` : str, default: null

  Similar to the `filename` option, this option sets a filename base
  component that will redirect (with a 302) to the current `filename`.
  This allows there to be a persistent known location that can be used
  if the `filename` option is dynamic or changes with revisions.

* ``{PREFIX}.inspect`` : str, default: /

  Specifies the top-level URL to start the application inspection at.

  TODO: this does not work.

  WARNING: this does not work.

  SERIOUSLY: this does not work, it only adds the specified path as a
  URL prefix... doh!

* ``{PREFIX}.include`` : list(regex-spec), default: null

  The `include` option lists encapsulated regular expressions that an
  endpoint must match at least one of in order to be included in the
  output. This option can be used with the `exclude` option, in which
  case endpoints are first matched for inclusion, then matched for
  exclusion (i.e. the order is "allow,deny" in apache terminology).

  Encapsulated regular expressions are expressed in the syntax
  "/EXPR/FLAGS", where the "/" can be replaced by any character
  otherwise not found in the rest of the expression. The flags can
  be any combination of the following characters:

  * ``i``: Case-insensitive matching.
  * ``l``: Use locale-dependent processing (for \w, \W, etc.).
  * ``m``: Multi-line mode, i.e. "^" and "$" match individual lines.
  * ``s``: The "." matches newlines as well.
  * ``u``: Use the unicode properties db (for \w, \W, etc.).
  * ``x``: Allow verbose regular expressions.

  Example:

  .. code-block:: ini

    describe.include = :^/api/:i :^/foo(/.*)?$:
    describe.exclude = :.*/private(/.*)?$:i

* ``{PREFIX}.exclude`` : list(regex-spec), default: null

  The inverse of the `include` option -- see `include` for details.

* ``{PREFIX}.entries.filters`` : list(resolve-spec), default: null

  This option specifies a callable (or string in python dot syntax) or
  list of thereof that filter and modify the entries before they are
  rendered to the requested format. Each entry that is selected for
  inclusion for rendering is first passed through each filter and
  replaced by the return value from the call. This is done for each
  filter consecutively. If any filter returns ``None``, the entry is
  removed from the selection list.

  These filters are intended to allow two primary features:

  * Access control: a filter can inspect the entry and the requesting
    user and determine if the entry should be made visible. If not, it
    should return ``None``.

  * Custom documentation parsing: a filter can parse the entry's `doc`
    attribute (which gets auto-populated with the entry's python
    documentation string), and extract other information such as
    expected parameters, return values, and exceptions thrown.
    Typically, this is done with something like numpydoc_.

  Filters are passed two parameters: an `entry` object (see
  pyramid_describe.entry.Entry for detailed attributes) and an
  `options` dictionary. The latter has many interesting attributes,
  including a reference to the current `request`.

  TODO: add documentation about `entry` and `options`.

  Note that there is a *separate* `filters` option that is used to
  filter the entire output document, which is format-specific. See
  the formatting options for details.

* ``{PREFIX}.formats`` : list(str), default: ['html', 'txt', 'pdf', 'rst', 'json', 'yaml', 'wadl', 'xml']

  Specifies the list of formats that can be generated. The default
  list includes all supported built-in formats, but this can be
  extended by adding a format to this list and then specifying a
  template to render the format. For example:

  .. code-block:: ini

    # declare support for HTML, JSON and SWF
    describe.formats = html json swf

    # HTML and JSON are built-in, but SWF needs a custom template
    describe.format.swf.renderer = mypackage:templates/describe-swf.mako

  Note that the "pdf" and "yaml" formats require that optional python
  package dependencies be installed (respectively `pdfkit` and
  `PyYAML`), and that pdfkit_ furthermore requires that the
  wkhtmltopdf_ program be available.

* ``{PREFIX}.format.default`` : str, default: first format listed in `{PREFIX}.formats`

  Set the default format if not specified in the request.

* ``{PREFIX}.format.{FORMAT}.renderer`` : asset-spec, default: 'pyramid_describe:template/{FORMAT}.mako'

  Override the default renderer for the specified format using a
  pyramid-style asset specification. The default is to use the
  pyramid-describe template with the exception of the structured
  data formats (JSON, YAML, XML, and WADL), which do not use a
  template.

  Specifying a renderer pre-empts all other rendering fallback
  mechanisms.

* ``{PREFIX}.format.request`` : { bool, list(str) }, default: false

  Specifies which options, if any, can be controlled by request
  parameters. The setting can either be a boolean ("true", "false",
  etc), or a list of options. If truthy, all options can be
  specified. If falsy, no options can be specified. Otherwise it
  is interpreted as a space-separated list of options that can be
  specified.

  Note that this setting can be overridden on a per-format basis
  by the `format.{FORMAT}.request` setting.

* ``{PREFIX}.format.{FORMAT}.request`` : { bool, list(str) }, default: none

  The per-format version of `format.request`. Note that this
  completely overrides the `format.request` setting for the
  given format, it does not extend it.

* ``{PREFIX}.format.default.{OPTION}``

  Set a default rendering option for all formats. Note that this can
  be overridden by request parameters (see the `format.request`
  option). See the `Options`_ section for a list of all supported
  options.

* ``{PREFIX}.format.override.{OPTION}``

  Set a rendering option for all formats that overrides any request
  parameters. See the `Options`_ section for a list of all supported
  options.

* ``{PREFIX}.format.{FORMAT}.default.{OPTION}``

  Set a default rendering option for the specified format, which
  overrides any default value set for all formats. Note that this can
  be overridden by request parameters (see the `format.request`
  option). See the `Options`_ section for a list of all supported
  options.

* ``{PREFIX}.format.{FORMAT}.override.{OPTION}``

  Set a rendering option for the specified format that overrides any
  request parameters and any generic format override options. See the
  `Options`_ section for a list of all supported options.


Options
=======

* ``showUnderscore`` : bool, default: false
* ``showUndoc`` : bool, default: true
* ``showLegend`` : bool, default: true
* ``showBranches`` : bool, default: false
* ``pruneIndex`` : bool, default: true
* ``showRest`` : bool, default: true
* ``showImpl`` : bool, default: false
* ``showInfo`` : bool, default: true
* ``showName`` : bool, default: true
* ``showDecorated`` : bool, default: true
* ``showExtra`` : bool, default: true
* ``showMethods`` : bool, default: true
* ``showIds`` : bool, default: true
* ``showDynamic`` : bool, default: true
* ``showGenerator`` : bool, default: true
* ``showGenVersion`` : bool, default: true
* ``showLocation`` : bool, default: true
* ``ascii`` : bool, default: false
* ``maxdepth`` : int, default: 1024
* ``width`` : int, default: 79
* ``maxDocColumn`` : int, default: null
* ``minDocLength`` : int, default: 20

* ``cssEmbed`` : bool, default: true
* ``cssPath`` : { asset-spec, resolve-spec, list({ asset-spec, resolve-spec }) }, default: 'pyramid_describe:template/rst2html.css'

* ``rstMax`` : bool, default: false
* ``rstPdfkit`` : bool, default: true

* ``stubFormat`` : str, default: '{{{}}}'
* ``dynamicFormat`` : str, default: '{}/?'
* ``restFormat`` : str, default: '<{}>'

* ``showOutline`` : bool, default: true
* ``pageGrayscale`` : bool, default: false
* ``pageSize`` : str, default: 'A4'
* ``pageOrientation`` : str, default: 'Portrait'
* ``pageMarginTop`` : str, default: '10mm'
* ``pageMarginRight`` : str, default: '10mm'
* ``pageMarginBottom`` : str, default: '10mm'
* ``pageMarginLeft`` : str, default: '10mm'

* ``restVerbs`` : list(str), default: pyramid_controllers.restcontroller.HTTP_METHODS

  Sets the list of known HTTP methods. This is used during inspection
  to determine whether a given exposed method on a RestController can
  be accessed via an HTTP method.

* ``filters`` : list(resolve-spec), default: null

  Unlike the top-level `entries.filters` setting which filters
  individual entries as they get selected for rendering, the
  format-specific `filters` option is called on the entire data object
  before final rendering, and is very format-specific in what is made
  available.

  For the structured-data formats (JSON, YAML, XML, and WADL), the
  filters are provided the data object created by
  Describer.structure_render. Each filter is expected to return that
  object (enhanced in some way), or a new object to replace it.

  For HTML, the filters are provided the result of calling
  `docutils.core.publish_parts
  <http://docutils.sourceforge.net/docs/api/publisher.html#publish-parts-details>`_
  during the transformation of rST to HTML. The following "parts" are
  then joined to form the downstream content, in order:

  * head_prefix
  * head
  * stylesheet
  * body_prefix
  * body_pre_docinfo
  * docinfo
  * body
  * body_suffix

  For PDF, rendering is accomplished from entries to rST to HTML to
  PDF. Therefore, the filtering occurs during the rST to HTML
  transformation.

  TODO: add documentation about `data` and `options`.

* ``encoding`` : str, default: 'UTF-8'

.. _pyramid-controllers: https://pypi.python.org/pypi/pyramid_controllers
.. _numpydoc: https://github.com/numpy/numpy/blob/master/doc/HOWTO_DOCUMENT.rst.txt
.. _pdfkit: https://pypi.python.org/pypi/pdfkit
.. _wkhtmltopdf: http://code.google.com/p/wkhtmltopdf/
