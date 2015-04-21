===================================
Self-Documentation for Pyramid Apps
===================================

A Pyramid plugin that makes a Pyramid application self-documenting via
inspection/reflection to:

1. Describe the application URL structure,
2. Extract documentation from Python comments, and
3. Generate formal syntax using commenting conventions.

The resulting documentation can be served by the application to an
HTTP request or displayed on the command line. It has built-in support
for plain-text hierachies, reStructuredText, HTML, PDF, JSON, YAML,
WADL, and XML, however other custom formats can be added easily.

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

.. note::

  Currently, pyramid-describe can only inspect the first Controller
  it finds -- this will eventually be fixed to correctly implement
  the `inspect` option.


Project Info
============

* Project Page: https://github.com/cadithealth/pyramid_describe
* Bug Tracking: https://github.com/cadithealth/pyramid_describe/issues


TL;DR
=====

Install:

.. code:: bash

  $ pip install pyramid-describe

Command-line example:

.. code:: bash

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

.. TODO - figure out how to serve these assets with the correct Content-Type...

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

Enable the plugin:

.. code:: python

  def main(global_config, **settings):
    # ...
    config.include('pyramid_describe')
    # ...

And make the documentation available publicly at "/describe":

.. code:: ini

   [app:main]
   describe.attach                          = /describe
   describe.formats                         = html pdf
   describe.format.html.default.cssPath     = myapp:style/doc-html.css
   describe.format.html+pdf.default.cssPath = myapp:style/doc-pdf.css
   describe.format.default.pdfkit.options   = {page-size: Letter}

Note that there are **many** options to control how the resulting
documentation is made available -- see Options_.


Installation
============

Install with the usual python mechanism, e.g. here with ``pip``:

.. code:: bash

  $ pip install pyramid-describe


Usage
=====

There are three mechanisms to use pyramid-describe: via standard
pyramid inclusion which will add routes to the current application, by
explicitly embedding a ``pyramid_describe.DescribeController``
instance, or by directly calling the ``pyramid_describe.Describer``
object methods.


Pyramid Inclusion
=================

Pyramid-describe can be added via standard pyramid inclusion, either
in the INI file or directly in your `main` function. For example:

.. code:: python

  def main(global_config, **settings):
    # ...
    config.include('pyramid_describe')

When using pyramid inclusion, pyramid-describe expects to find
configuration options in the application settings. See the `Options`_
section for a list of all supported options, with a short example
here:

.. code:: ini

  [app:main]

  describe.attach                        = /doc
  describe.formats                       = html json pdf
  describe.format.default.title          = My Application
  describe.format.html.default.cssPath   = myapp:static/doc.css
  describe.entries.filters               = myapp.describe.entry_filter

Note that multiple describers, each with different configurations, can
be added via pyramid inclusion by using the `describe.prefixes`
option.


DescribeController
==================

Pyramid-describe can also be added to your application by embedding a
DescribeController object. The DescribeController constructor takes
the following parameters:

`view`:

  An instance of ``pyramid.interfaces.IView``, which is the view that
  should be inspected and reflected.

`root`:

  The root path to the specified URL, so that host-relative URLs can
  be generated to the views found.

`settings`:

  A dictionary of all the options to apply to this describer. Note that
  in this case, the options should not have any prefix.

Example:

.. code:: python

  from pyramid_describe import DescribeController

  def main(global_config, **settings):
    # ...
    config.include('pyramid_controllers')

    settings = {
      'formats'                       : ['html', 'json', 'pdf'],
      'format.default.title'          : 'My Application',
      'format.html.default.cssPath'   : 'myapp:static/doc.css',
      'entries.filters'               : 'myapp.describe.entry_filter',
    }

    config.add_controller('MyAppDescriber', '/doc', DescribeController(settings))


Describer
=========

Pyramid-describe can also be added to your application by directly
calling the Describer's functionality. This is an even lower-level
approach than, but still quite similar to, embedding the
`DescribeController`_; the constructor takes the same `settings`
parameter as the DescribeController, and then a call to the `describe`
method actually generates the output. The `describe` method takes as
parameters a `context` and a `format`, and returns a dictionary with
the following attributes:

.. TODO - document `context` and `format`...

`content_type`:

  The MIME content-type associated with the rendered output.

`charset`:

  The character set that the output is encoded in.

`content`:

  The actual rendering output.

Example:

.. code:: python

  from pyramid_describe import Describer

  def my_describer(request):

    settings = {
      'formats'                       : ['html', 'json', 'pdf'],
      'format.default.title'          : 'My Application',
      'format.html.default.cssPath'   : 'myapp:static/doc.css',
      'entries.filters'               : 'myapp.describe.entry_filter',
    }

    describer = Describer(settings=settings)
    context   = dict(request=request)
    result    = describer.describe(context=context, format='pdf')

    request.response.content_type = result['content_type']
    request.response.charset      = result['charset']
    request.response.body         = result['content']

    return request.response


Documentation Conventions
=========================

By default, the documentation that is extracted from your handlers'
pydocs is parsed and converted using:

* Docorator extraction
* Common text-role definitions
* Field-list aliasing of numpydoc sections
* Numpydoc parsing
* Inter-endpoint linking and referencing

This behavior can be disabled or extended by setting the
`entries.parsers` setting (see Options_). Here is an example that
employs each of these functions (see below for an in-depth
explanation):

.. code:: python

  class MyController(RestController):

    @expose
    def deactivate(self, request):
      '''
      @PUBLIC, @DEPRECATED(1.3.23)

      The current object is deleted. Please note that this endpoint is
      deprecated; please use the more RESTful :doc.link:`DELETE:..`
      endpoint instead.

      @INTERNAL: OOPS! This method was accidentally carried over from
      the Java implementation. The `soap-to-rest` tool needs to be
      analyzed to figure out why this happened.

      :doc.copy:`DELETE:..`
      '''

    @expose
    def get(self, request):
      '''
      :doc.import:`myapp:doc/mycontroller.rst`
      '''

    @expose
    def delete(self, request):
      '''
      @PUBLIC, @FROZEN

      The current object is deleted.

      :Parameters:

      recursive : bool, optional, default: false

        If true, recursively deletes any dependent objects too.

      permanent : bool, optional, default: false, @INTERNAL

        If true, the objects and all records are permanently purged
        from the network. Reserved for internal administrators.

      :Returns:

      HTTPOk

        The object(s) were successfully deleted.

      :Raises:

      HTTPForbidden

        The current user does not have sufficient privileges.

      HTTPNotFound

        The specified object does not exist.
      '''


Docorator Extraction
--------------------

Docorators are decorators for documentation. For example, you may
decorate a particular endpoint with ``@BETA`` to declare that this
endpoint is not finalized yet.

Pyramid-describe will inspect an entry's ``.doc`` text and convert
them to class names. The class names are applied to different element
levels depending on where they are found:

* Docorators on the first line apply to the entire entry.

* Docorators at the beginning of a paragraph apply to that paragraph
  only.

* Docorators at the beginning of a section title apply to that
  section.

* Docorators in the numpydoc `type` specification apply to that
  parameter/return/raise or other formal numpydoc object.

Docorators must follow one of the following syntaxes:

* Simple tag style: ``@TAG``, where ``TAG`` can be any alphanumeric
  sequence.

* Parameterized declaration style: ``@TAG(PARAMS)``, where ``TAG`` can
  be any alphanumeric sequence, and ``PARAMS`` can be anything except
  the closing parenthesis.

Docorators are converted to class names using the following rules:

* Prefixed with ``doc-``.

* All letters are lowercased.

* All non-alphanumeric characters are replaced with a dash ("-").

* Consecutive dashes are replaced with one dash.

* Terminating dashes are dropped.

Thus the docorator ``@DEPRECATED(1.3.23)`` becomes
``doc-deprecated-1-3-23``.

**IMPORTANT**: pyramid-describe does not apply any special processing
to docorators beyond identifying them and applying the class names to
the appropriate content. It is therefore up to the calling application
to filter these in any way, for example hiding entries (or portions
thereof) that have the ``doc-internal``, i.e. that were marked with
``@INTERNAL``.


Common Text-Role Definitions
----------------------------

The text-roles `class`, `meth`, and `func` are not by default defined
by docutils_. Pyramid-describe gives a *very* bare-bones
implementation (it just aliases them as "literal" style nodes). If
these text-roles are used by the calling application, a more thorough
implementation (that actually performs linking to API documentation)
is probably desirable. Pyramid-describe does not have access to this
information and is therefore outside of its scope.


Field List Aliasing of Sections
-------------------------------

All of the section headers that are specially processed by numpydoc
can also be specified as lone "field list" elements. For example, the
following two declarations are treated identically:

.. code:: python

   def function_name(self, request):
     '''
     Parameters
     ----------

     This endpoint does not take any parameters.
     '''

.. code:: python

   def function_name(self, request):
     '''
     :Parameters:

     This endpoint does not take any parameters.
     '''

The list of supported headers is extracted at runtime from
``numpydoc.docscrape.NumpyDocString()._parsed_data.keys()``.


Numpydoc
--------

By default, the pydoc text is parsed by numpydoc, and the Parameters,
Other Parameters, Returns, and Raises sections are extracted and
converted into formal structured properties of the entry. See
numpydoc_ for format and syntax details.


Inter-Endpoint Linking
----------------------

Pyramid-describe allows for entry documentation to refer and link to
other endpoint documentation. Specifically, the following text-roles
are provided:

* ``:doc.link:\`[METHOD:]PATH\```:

  Links to the specified endpoint. If ``METHOD`` is specified, then
  the link points directly to that HTTP method. ``PATH`` can be either
  absolute (i.e. starting with a slash ``/``) or relative
  (i.e. starting with either ``./`` or ``../``). Note that unlike
  "href" syntax, ``./`` refers to the current endpoint, not the
  current endpoint's parent. Some examples, assuming the current
  endpoint is ``/foo/bar``:

  * ``:doc.link:\`GET:/index\```: links to the GET method of "/index"
  * ``:doc.link:\`PUT:.\```: links to the PUT method of "/foo/bar"
  * ``:doc.link:\`POST:./zog\```: links to the POST method of "/foo/bar/zog"
  * ``:doc.link:\`POST:../zog\```: links to the POST method of "/foo/zog"

* ``:doc.copy:\`[METHOD:]PATH[:SECTION]\```:

  Inlines the specified remote endpoint's documentation here. The
  ``METHOD`` and ``PATH`` apply as for ``:doc.link:\`...\```. The
  optional ``SECTION`` parameter is a comma-separated list of which
  sections to inline -- if not specified or empty, the entire
  endpoint's documentation is inlined; if the wildcard ``*``, then all
  named sections are inlined, but not the main description.

  Note that section referencing will only work correctly if the
  entries are decorated with the parsed sections. This is one of the
  things that numpydoc-style parsing does when enabled (so don't
  disable it! :-).

* ``:doc.import:\`ASSET-SPEC\```:

  Inlines the specified asset, which is loaded using either
  pkg_resources or python import. When using pkg_resources, the spec
  must be in the format ``[PACKAGE:]PATH``. If the PACKAGE is omitted,
  then the PATH is taken to be relative to the current module.

  If the asset cannot be loaded using pkg_resources, a standard python
  import is tried. If this succeeds, it is either called (if callable)
  with no arguments or cast to a string with ``str(symbol)``.

Note that sometimes it useful to have aliases to above
text-roles. This can be achieved by registering the alias text-roles.
The following will alias ``api`` to ``doc.link``:

.. code:: python

  from docutils.parsers.rst import roles
  from pyramid_describe.syntax.docref import textrole_doc_link

  roles.register_generic_role('api', textrole_doc_link)


Options
=======

The configuration of pyramid-describe is done by setting any of the
following options. Note that if specified in the application settings
(i.e. the INI file), then they must be prefixed with (by default)
``describe.``. Otherwise, when passing a dictionary of settings to the
constructors, the prefix is left off. The following options exist:

* ``describe.prefixes`` : list(str), default: 'describe'

  Defines the prefix or the list of prefixes that pyramid-describe
  settings will be searched for in the configuration. For each prefix,
  a separate DescribeController will be created and attached to the
  application router. The following example attaches two controllers
  at ``/desc-one`` and ``/desc-two``:

  .. code:: ini

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

  .. code:: text

    http://localhost:8080/describe/application.txt
    http://localhost:8080/describe/application.json
    http://localhost:8080/describe?format=json

* ``{PREFIX}.fullname`` : str, default: 'application'

  Sets the filename (excluding the extension) that the output will be
  served at using the DescribeController. The extension provided by
  the request will determine which format to serve, and must be listed
  in the `formats` option. If the format is not listed, a 404 is
  returned. Typically, this is set to the application's name and
  might also include the application version.

* ``{PREFIX}.basename`` : str, default: null

  Similar to the `fullname` option, this option sets a filename base
  component that will either redirect to the current `fullname` or
  actually serve the content based on the `base-redirect` option. This
  allows there to be a persistent known location that can be used if
  the `filename` option is dynamic or changes with revisions.

* ``{PREFIX}.index-redirect`` : { bool, int, str }, default: true

  Controls what happens when a request comes to the index location
  of the DescribeController, i.e. the value of the `attach` option.
  The following values are accepted:

  falsy

    Responds with the actual content using the default format.

  truthy

    Redirects with a 302 to the `basename` if set, otherwise to
    the `fullname`, using the default format's extension.

  int

    Same as if truthy, but uses the specified response code (e.g.
    301 instead of 302).

  str

    Responds with a redirect using the specified string as the
    ``Location`` header. By default, issues a 302 unless the string is
    prefixed with the code and a space, e.g. ``301
    /path/to/filename``. If the location is not absolute, it will be
    evaluated relative to the current URL.

* ``{PREFIX}.base-redirect`` : { bool, int, str }, default: true

  If `basename` is set, then this controls how the response is handled
  -- see the `index-redirect` option for accepted values, with the
  adjustment that the default redirect location is the `fullname`.

* ``{PREFIX}.inspect`` : str, default: /

  Specifies the top-level URL to start the application inspection at.

  IMPORTANT: this is not currently implemented the way that it should
  be... the current workaround simply adds the specified path (and its
  descendants) to the `include` list.

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

  .. code:: ini

    describe.include = :^/api/:i :^/foo(/.*)?$:
    describe.exclude = :.*/private(/.*)?$:i

* ``{PREFIX}.exclude`` : list(regex-spec), default: null

  The inverse of the `include` option -- see `include` for details.

* ``{PREFIX}.entries.parsers`` : list(resolve-spec), default: 'pyramid_describe.syntax.default'

  This option specifies a callable (or string in python dot syntax) or
  list thereof that modify the entries before they are rendered. These
  parsers are intended to augment the documentation in some way. For
  example, formal syntax documentation may be extracted from the
  plain-text documentation. Or special short-hand syntax can be
  converted to standard reStructuredText format.

  Each entry that is selected for inclusion for rendering is first
  passed through each parser and replaced by the return value from the
  call. This is done for each parser consecutively. If any parser
  returns ``None``, the entry is removed from the selection list.

  By default, the 'pyramid_describe.syntax.default' parser is applied,
  which works as described in `Documentation Conventions`_. This
  default parser can be disabled (by setting this option to null),
  replaced (by setting this option to another callable), or extended
  (by setting this option to the default and appending any custom
  parsers to it).

  Parsers are passed two parameters: an `entry` object (see
  pyramid_describe.entry.Entry for detailed attributes) and an
  `options` dictionary.

  Note that the `entry` object may represent either a single method of
  an endpoint, or the entire endpoint. The methods will be sent
  through the parser before the entire endpoint.

  TODO: add documentation about `entry` and `options`.

  The result of a parser operation is expected to be cacheable; this
  means that it should only be sensitive to the data in the actual
  entry itself, not the current request. For that, see the
  `entries.filters` option.

  TODO: although the `options` object currently includes a reference
  to the current `request`, this should not be assumed -- it will
  likely be removed as entry parsing (but not rendering) may be done
  pro-actively at some point (i.e. when there is no request).

  Each parser must be a callable; if it is not, then the object's
  ``parser`` attribute will be tried instead. This allows the option
  to specify just the name of a module that contains a ``def
  parser(...): ...`` function definition.

* ``{PREFIX}.entries.filters`` : list(resolve-spec), default: null

  This option is identical in syntax to the `entries.parsers` option,
  is called with the same parameters, and is expected to have the
  same return type.

  The crucial difference, however, is that the result of the filters
  is not expected to be cacheable. Therefore, a filter is the more
  appropriate place to do access control: entries (or sections
  thereof) can be removed (by returning ``None``) or modified in any
  way (by returning a modified entry).

  Note that parsers and filters typically work together in this
  respect by, for example, having the parser decorate the entry with
  classes that the filter then inspects.

  Note that there is a *separate* `filters` option that is used to
  filter the entire output document, which is format-specific. See
  the formatting options for details.

* ``{PREFIX}.methods.order`` : list(str), default: ['post', 'get', 'put', 'delete']

  Sets the order that endpoint methods are listed in. By default,
  it is in CRUD + alphabetic order, i.e. that CRUD methods (POST,
  GET, PUT, DELETE) are listed first, then all other methods are
  listed alphabetically thereafter.

* ``{PREFIX}.render.template`` : asset-spec, default: null

  Overrides the rendering of the endpoints from separate units into
  one document. By default, the document is rendered as a simple
  document with a title, a section for the endpoints, and the legend.

  However, this document can also be generated using a pyramid
  template using the ``render.template`` option, as long as it outputs
  reStructuredText. To include the documentation generated by the
  endpoints, the ``doc.endpoint`` directive is used.

  The `doc.endpoint` directive takes a single argument that can have
  any of the following formats:

  * ``.. doc.endpoint:: GLOB``:

    Specifies than the documentation for any endpoint whose path
    matches the specified ``GLOB`` pattern should replace the
    directive. The GLOB syntax uses globre_ rules, basically that
    ``*`` matches zero or more characters except ``/``, ``**`` matches
    zero or more of any character (including ``/``), and ``?`` matches
    any single character except ``/`` (there are some other rules too
    -- see globre_ for details). One additional rule specific to
    pyramid-describe is that ``/**`` at the end of a pattern matches a
    path without the trailing ``/`` as well.

  * ``.. doc.endpoint:: regex:EXPR``:

    Specifies a regular expression to match against the path of all
    endpoints to be included.

  * ``.. doc.endpoint:: unmatched:EXPR``

    Identical to the ``regex:EXPR`` format, except only endpoints
    that match the expression AND that have not already been included
    previously in the document are now included.

  * ``.. doc.endpoint:: unmatched``

    Matches and includes all endpoints that have not been included
    yet.

  The template is provided the same `data`, `options` and `request`
  parameters as other filters.

  Note that the output from this rendering is NOT cached, and it is
  therefore acceptable at this point to render request-specific
  output.

  An example; the following configuration:

  .. code:: ini

    describe.render.template = myapp:template/docs.mako

  would use the Mako templating engine (standard Pyramid template
  engine selection is performed) to parse and render the
  `template/docs.mako` file inside the `myapp` module. This template
  can leverage all the standard Mako syntax, as long as it outputs
  valid reStructuredText. An example template:

  .. code:: mako

    =========================
    Application Documentation
    =========================

    <%! import time %>
    Rendered on: ${time.asctime()}.

    Public Endpoints
    ================

    .. doc.endpoint:: regex:^/public(/.*)?$

    Other Endpoints
    ===============

    .. doc.endpoint:: unmatched

    <%include file="othe-docs-and-copyright.mako"/>

* ``{PREFIX}.formats`` : list(str), default: ['html', 'txt', 'pdf', 'rst', 'json', 'yaml', 'wadl', 'xml']

  Specifies the list of formats that can be generated. The default
  list includes all supported built-in formats, but this can be
  extended by adding a format to this list and then specifying a
  template to render the format. For example:

  .. code:: ini

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

  See `Format Cascading`_ for details on how the `{FORMAT}` string is
  evaluated.

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

  See `Format Cascading`_ for details on how the `{FORMAT}` string is
  evaluated.

* ``{PREFIX}.format.default.{OPTION}``

  Set a default rendering option for all formats. Note that this can
  be overridden by request parameters (see the `format.request`
  option). See the `Format Options`_ section for a list of all
  supported options.

* ``{PREFIX}.format.override.{OPTION}``

  Set a rendering option for all formats that overrides any request
  parameters. See the `Format Options`_ section for a list of all
  supported options.

* ``{PREFIX}.format.{FORMAT}.default.{OPTION}``

  Set a default rendering option for the specified format, which
  overrides any default value set for all formats. Note that this can
  be overridden by request parameters (see the `format.request`
  option). See the `Format Options`_ section for a list of all
  supported options.

  See `Format Cascading`_ for details on how the `{FORMAT}` string is
  evaluated.

* ``{PREFIX}.format.{FORMAT}.override.{OPTION}``

  Set a rendering option for the specified format that overrides any
  request parameters and any generic format override options. See the
  `Format Options`_ section for a list of all supported options.

  See `Format Cascading`_ for details on how the `{FORMAT}` string is
  evaluated.


Format Cascading
================

Some formats are rendered based on the output of other renderers. For
example, PDF's are generated from HTML, and HTML is in turn generated
from reStructuredText. Because options may need to be different for
the the various formats based on the ultimate output, there is the
ability to specify "cascaded" formats by joining them with a "+" in
the settings. The cascaded options can either be explicitly overriden
or explicitly reverted to their system-wide default by setting them to
the special value ``pyramid_describe:DEFAULT``.

Therefore, options for format "rst" apply to the reStructuredText
rendering, regardless of ultimate output. Options for format
"rst+html" apply to reStructuredText rendering, but only if the next
renderer is "html". These can be chained to any depth, for example
options for format "rst+html+pdf" apply to reStructuredText rendering,
but only if the next renderer is "html" followed by "pdf". Note that
one cannot skip a renderer in a rendering pipeline, e.g. in the
previous case, you cannot short-hand the format as "rst+pdf".

For example, the following configuration will apply a different CSS to
the HTML rendering based on whether the output is going to be HTML,
PDF, or SWF:

.. code:: ini

   # the following sets the `cssPath` option for *any* HTML rendering:
   describe.format.html.default.cssPath = myapp:style/rst2html.css

   # this now overrides the `cssPath` option during rendering of the
   # HTML, but only in the context of a PDF rendering:
   describe.format.html+pdf.default.cssPath = myapp:style/rst2pdf.css

   # when generating SWFs, this tells the describer to revert to using
   # the system default value of `cssPath`:
   describe.format.html+swf.default.cssPath = pyramid_describe:DEFAULT


Format Options
==============

* ``title`` : str, default: 'Contents of "{PATH}"'
* ``endpoints.title`` : str, default: 'Endpoints'
* ``legend.title`` : str, default: 'Legend'

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

* ``pdfkit.options`` : yaml-str

  This option is YAML-parsed, and then sets the options that are
  inserted into the HTML meta tags that are instructions to the pdfkit
  processor. The default values specified by pyramid-describe are:

  .. code:: text

    {
      margin-top: 10mm,
      margin-right: 10mm,
      margin-bottom: 10mm,
      margin-left: 10mm,
    }

  Options not specified revert to the defaults specified by pdfkit.
  For details, see `pdfkit <https://pypi.python.org/pypi/pdfkit>`_
  and `wkhtmltopdf <http://code.google.com/p/wkhtmltopdf/>`_. Options
  that may be of interest:

  * grayscale
  * page-size
  * orientation
  * no-outline
  * print-media-type
  * zoom
  * javascript-delay
  * disable-javascript

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

  For RST and HTML, the filters are provided a
  `docutils.nodes.document` object (as is returned by
  `docutils.core.publish_doctree
  <http://docutils.sourceforge.net/docs/api/publisher.html#publish-doctree>`_).

  For PDF, rendering is accomplished from entries to RST to HTML to
  PDF. Therefore, the filtering occurs during the RST to HTML
  transformation -- there is no separate PDF-only filtering. If
  filtering is needed at one of the previous stages that is required
  only during PDF generation (but not, for example, to HTML), then the
  `formatstack` option can be inspected, which will include ``'pdf'``
  during the HTML filtering. For example:

  .. code:: python

    def html_filter(doc, stage):
      if 'pdf' in stage.options.formatstack:
        # do PDF-specific filtering...
      else:
        # do filtering for everything except PDF...
      return doc

  TODO: add documentation about `data` and `options`.

* ``encoding`` : str, default: 'UTF-8'

.. _pyramid-controllers: https://pypi.python.org/pypi/pyramid_controllers
.. _numpydoc: https://github.com/numpy/numpy/blob/master/doc/HOWTO_DOCUMENT.rst.txt
.. _pdfkit: https://pypi.python.org/pypi/pdfkit
.. _wkhtmltopdf: http://code.google.com/p/wkhtmltopdf/
.. _docutils: http://docutils.sourceforge.net/
.. _globre: https://pypi.python.org/pypi/globre
