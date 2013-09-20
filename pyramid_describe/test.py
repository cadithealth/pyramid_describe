# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2013/09/09
# copy: (C) Copyright 2013 Cadit Health Inc., All Rights Reserved.
#------------------------------------------------------------------------------

import sys, re, unittest, json, unittest, six
import xml.etree.ElementTree as ET
from webtest import TestApp

from pyramid import testing
from pyramid.request import Request
from pyramid.response import Response
from pyramid.httpexceptions import \
    HTTPNotFound, HTTPFound, HTTPMethodNotAllowed, \
    HTTPException, WSGIHTTPException
from pyramid_controllers import \
    Controller, RestController, \
    expose, index, lookup, default, fiddle
from pyramid_controllers.test_helpers import TestHelper
from pyramid_controllers.util import getVersion

from pyramid_describe.util import adict
from pyramid_describe.controller import DescribeController

# make the XML namespace output a bit easier to grok...
ET.register_namespace('wadl', 'http://research.sun.com/wadl/2006/10')
ET.register_namespace('xsd',  'http://www.w3.org/2001/XMLSchema')
ET.register_namespace('xsi',  'http://www.w3.org/2001/XMLSchema-instance')
ET.register_namespace('pd',   'http://pythonhosted.org/pyramid_describer/xmlns/0.1/doc')

class Rest(RestController):
  'A RESTful entry.'
  @expose
  def get(self, request):
    'Gets the current value.'
    return 'get!'
  @expose
  def put(self, request):
    'Updates the value.'
    return 'put!'
  @expose
  def post(self, request):
    'Creates a new entry.'
    return 'post!'
  @expose
  def delete(self, request):
    'Deletes the entry.'
    return 'delete!'
class SubIndex(Controller):
  @index(forceSlash=False)
  def myindex(self, request):
    'A sub-controller providing only an index.'
    return 'my.index'
class Sub(Controller):
  'A sub-controller.'
  @expose
  def method(self, request):
    'This method outputs a JSON list.'
    return '[3, "four"]'
  def helper(self): return 'not exposed'
class Unknown(Controller):
  'A dynamically generated sub-controller.'
class SimpleRoot(Controller):
  'A SimpleRoot controller (docs should come from index).'
  @index
  def index(self, request):
    'The default root.'
    return 'root.index'
  rest = Rest()
  sub  = Sub()
  swi  = SubIndex()
  unknown = Unknown

def docsEnhancer(entry, options):
  if entry and entry.path == '/swi':
    entry.classes = ['sub-with-index']
    return entry
  if not entry or entry.path != '/rest?_method=POST':
    return entry
  entry.classes = ['post-is-not-put', 'fake-docs-here']
  entry.params = (
    adict(id='param-_2Frest_3F_5Fmethod_3DPOST-size', name='size', type='int',
          default=4096, optional=True, doc='The anticipated maximum size'),
    adict(id='param-_2Frest_3F_5Fmethod_3DPOST-text', name='text', type='str',
          optional=False, doc='The text content for the posting'),
    )
  entry.returns = (adict(id='return-_2Frest_3F_5Fmethod_3DPOST-0-str', type='str',
                         doc='The ID of the new posting'),)
  entry.raises  = (
    adict(id='raise-_2Frest_3F_5Fmethod_3DPOST-0-HTTPUnauthorized',
          type='HTTPUnauthorized', doc='Authenticated access is required'),
    adict(id='raise-_2Frest_3F_5Fmethod_3DPOST-1-HTTPForbidden',
          type='HTTPForbidden', doc='The user does not have posting privileges'),
    )
  return entry

settings_minRst = {
  'exclude': '|^/desc(/.*)?$|',
  'index-redirect': 'false',
  'format.default': 'rst',
  'format.default.showLegend': 'false',
  'format.default.showMeta': 'false',
  }

#------------------------------------------------------------------------------
class DescribeTest(TestHelper):

  maxDiff = None

  #----------------------------------------------------------------------------
  def test_example(self):
    from .test_example import RootController, main
    # TODO: this is ridiculous...
    def ridiculous_init_override(self):
      super(RootController, self).__init__()
      self.desc = DescribeController(
        view=self, root='/',
        settings={
          'formats': 'txt',
          'index-redirect': 'false',
          'exclude': '|^/desc(/.*)?$|',
          })
    RootController.__init__ = ridiculous_init_override
    # /TODO
    self.app = main({})
    self.testapp = TestApp(self.app)
    res = self.testapp.get('/desc')
    self.assertMultiLineEqual(res.body, '''\
/                       # The application root.
├── contact/            # Contact manager.
│   ├── <POST>          # Creates a new 'contact' object.
│   └── {CONTACTID}     # RESTful access to a specific contact.
│       ├── <DELETE>    # Delete this contact.
│       ├── <GET>       # Get this contact's details.
│       └── <PUT>       # Update this contact's details.
├── login               # Authenticate against the server.
└── logout              # Remove authentication tokens.
''')

  #----------------------------------------------------------------------------
  def test_autodescribe_format_txt(self):
    'The Describer can render a plain-text hierarchy'
    root = SimpleRoot()
    # todo: yaml and pdf are not always there...
    root.desc = DescribeController(
      root, doc='URL \t  tree\n    description.',
      settings={
        'index-redirect': 'false',
        })
    self.assertResponse(self.send(root, '/desc/application.txt'), 200, '''\
/                           # The default root.
├── desc/                   # URL tree description.
│   ├── application.html
│   ├── application.json
│   ├── application.pdf
│   ├── application.rst
│   ├── application.txt
│   ├── application.wadl
│   ├── application.xml
│   └── application.yaml
├── rest                    # A RESTful entry.
│   ├── <DELETE>            # Deletes the entry.
│   ├── <GET>               # Gets the current value.
│   ├── <POST>              # Creates a new entry.
│   └── <PUT>               # Updates the value.
├── sub/
│   └── method              # This method outputs a JSON list.
├── swi                     # A sub-controller providing only an index.
└── unknown/?               # A dynamically generated sub-controller.
''')

  #----------------------------------------------------------------------------
  def test_autodescribe_format_txt_asciisettings(self):
    'The Describer can limit plain-text to 7-bit ASCII characters only (via global settings)'
    root = SimpleRoot()
    root.desc = DescribeController(
      root, doc='URL \t  tree\n    description.',
      settings={
        'exclude': '|^/desc(/.*)?$|',
        'index-redirect': 'false',
        'format.default.ascii': 'true',
        })
    self.assertResponse(self.send(root, '/desc/application.txt'), 200, '''\
/                   # The default root.
|-- rest            # A RESTful entry.
|   |-- <DELETE>    # Deletes the entry.
|   |-- <GET>       # Gets the current value.
|   |-- <POST>      # Creates a new entry.
|   `-- <PUT>       # Updates the value.
|-- sub/
|   `-- method      # This method outputs a JSON list.
|-- swi             # A sub-controller providing only an index.
`-- unknown/?       # A dynamically generated sub-controller.
''')

  #----------------------------------------------------------------------------
  def test_autodescribe_format_txt_asciiquerystring(self):
    'The Describer can limit plain-text to 7-bit ASCII characters only (via query-string)'
    root = SimpleRoot()
    root.desc = DescribeController(
      root, doc='URL \t  tree\n    description.',
      settings={
        'format.request': 'true',
        'index-redirect': 'false',
        'exclude': '|^/desc(/.*)?$|',
        })
    self.assertResponse(self.send(root, '/desc/application.txt?ascii=true'), 200, '''\
/                   # The default root.
|-- rest            # A RESTful entry.
|   |-- <DELETE>    # Deletes the entry.
|   |-- <GET>       # Gets the current value.
|   |-- <POST>      # Creates a new entry.
|   `-- <PUT>       # Updates the value.
|-- sub/
|   `-- method      # This method outputs a JSON list.
|-- swi             # A sub-controller providing only an index.
`-- unknown/?       # A dynamically generated sub-controller.
''')

  #----------------------------------------------------------------------------
  def test_option_filename(self):
    'The DescribeController can use a URL path other than "application.{EXT}"'
    root = SimpleRoot()
    root.desc = DescribeController(
      root, doc='URL \t  tree\n    description.',
      settings={
        'exclude': '|^/desc(/.*)?$|',
        'index-redirect': 'false',
        'format.default.ascii': 'true',
        'fullname': 'app',
        })
    self.assertResponse(self.send(root, '/desc/app.txt'), 200, '''\
/                   # The default root.
|-- rest            # A RESTful entry.
|   |-- <DELETE>    # Deletes the entry.
|   |-- <GET>       # Gets the current value.
|   |-- <POST>      # Creates a new entry.
|   `-- <PUT>       # Updates the value.
|-- sub/
|   `-- method      # This method outputs a JSON list.
|-- swi             # A sub-controller providing only an index.
`-- unknown/?       # A dynamically generated sub-controller.
''')

  #----------------------------------------------------------------------------
  def test_other_paths_404(self):
    'The DescribeController responds with 404 for unknown path requests'
    root = SimpleRoot()
    root.desc = DescribeController(
      root, doc='URL \t  tree\n    description.',
      settings={
        'exclude': '|^/desc(/.*)?$|',
        'index-redirect': 'false',
        })
    self.assertResponse(self.send(root, '/desc/app.txt'), 404)

  #----------------------------------------------------------------------------
  def test_option_redirect(self):
    'The DescribeController can expose a persistent path that redirects to the "real" location'
    root = SimpleRoot()
    root.desc = DescribeController(
      root, doc='URL \t  tree\n    description.',
      settings={
        'exclude': '|^/desc(/.*)?$|',
        'formats': 'txt yaml wadl',
        'fullname': 'app-v0.3',
        'basename': 'app',
        })
    self.assertResponse(self.send(root, '/desc/app.txt'),  302,
                        location='http://localhost/desc/app-v0.3.txt')
    self.assertResponse(self.send(root, '/desc/app.yaml'), 302,
                        location='http://localhost/desc/app-v0.3.yaml')
    self.assertResponse(self.send(root, '/desc/app.wadl'), 302,
                        location='http://localhost/desc/app-v0.3.wadl')
    self.assertResponse(self.send(root, '/desc/app.json'), 404)
    self.assertResponse(self.send(root, '/desc/app.html'), 404)
    self.assertResponse(self.send(root, '/desc/app.xml'),  404)
    self.assertResponse(self.send(root, '/desc'),  302,
                        location='http://localhost/desc/app.txt')
    self.assertResponse(self.send(root, '/desc/'),  302,
                        location='http://localhost/desc/app.txt')
    self.assertResponse(self.send(root, '/desc?q=23'),  302,
                        location='http://localhost/desc/app.txt?q=23')
    self.assertResponse(self.send(root, '/desc/?q=23'),  302,
                        location='http://localhost/desc/app.txt?q=23')
    self.assertResponse(self.send(root, '/desc?redirect=false'),  200)
    self.assertResponse(self.send(root, '/desc/?redirect=false'),  200)

  #----------------------------------------------------------------------------
  def test_option_indexredirect_nobasename(self):
    'The DescribeController redirects the index request to the fullname when no basename'
    root = SimpleRoot()
    root.desc = DescribeController(
      root, doc='URL \t  tree\n    description.',
      settings={
        'exclude': '|^/desc(/.*)?$|',
        'formats': 'txt yaml wadl',
        'fullname': 'app-v0.3',
        })
    self.assertResponse(self.send(root, '/desc'),  302,
                        location='http://localhost/desc/app-v0.3.txt')
    self.assertResponse(self.send(root, '/desc/'),  302,
                        location='http://localhost/desc/app-v0.3.txt')
    self.assertResponse(self.send(root, '/desc?q=23'),  302,
                        location='http://localhost/desc/app-v0.3.txt?q=23')
    self.assertResponse(self.send(root, '/desc/?q=23'),  302,
                        location='http://localhost/desc/app-v0.3.txt?q=23')
    self.assertResponse(self.send(root, '/desc?redirect=false'),  200)
    self.assertResponse(self.send(root, '/desc/?redirect=false'),  200)

  #----------------------------------------------------------------------------
  def test_option_indexredirect_301(self):
    'The DescribeController index redirect option allows 301'
    root = SimpleRoot()
    root.desc = DescribeController(
      root, doc='URL \t  tree\n    description.',
      settings={
        'exclude': '|^/desc(/.*)?$|',
        'formats': 'txt yaml wadl',
        'fullname': 'app-v0.3',
        'index-redirect': '301',
        })
    self.assertResponse(self.send(root, '/desc'),  301,
                        location='http://localhost/desc/app-v0.3.txt')

  #----------------------------------------------------------------------------
  def test_option_indexredirect_expliciturl(self):
    'The DescribeController index redirect option allows explicit URL'
    root = SimpleRoot()
    root.desc = DescribeController(
      root, doc='URL \t  tree\n    description.',
      settings={
        'exclude': '|^/desc(/.*)?$|',
        'formats': 'txt yaml wadl',
        'fullname': 'app-v0.3',
        'index-redirect': 'https://example.com/path/filename#anchor',
        })
    self.assertResponse(self.send(root, '/desc'),  302,
                        location='https://example.com/path/filename#anchor')

  #----------------------------------------------------------------------------
  def test_option_indexredirect_expliciturl_301(self):
    'The DescribeController index redirect option allows explicit URL'
    root = SimpleRoot()
    root.desc = DescribeController(
      root, doc='URL \t  tree\n    description.',
      settings={
        'exclude': '|^/desc(/.*)?$|',
        'formats': 'txt yaml wadl',
        'fullname': 'app-v0.3',
        'index-redirect': '301 https://example.com/path/filename#anchor',
        })
    self.assertResponse(self.send(root, '/desc'),  301,
                        location='https://example.com/path/filename#anchor')

  #----------------------------------------------------------------------------
  def test_option_indexredirect_expliciturl_relative(self):
    'The DescribeController index redirect option allows explicit URL'
    root = SimpleRoot()
    root.desc = DescribeController(
      root, doc='URL \t  tree\n    description.',
      settings={
        'exclude': '|^/desc(/.*)?$|',
        'formats': 'txt yaml wadl',
        'fullname': 'app-v0.3',
        'index-redirect': '../another/location',
        })
    self.assertResponse(self.send(root, '/desc'), 302,
                        location='http://localhost/another/location')

  #----------------------------------------------------------------------------
  def test_include(self):
    'Setting the Describer `include` parameter is exclusive'
    root = SimpleRoot()
    root.desc = DescribeController(
      root, doc='URL tree description.',
      settings={
        'formats': 'txt',
        'index-redirect': 'false',
        'include': '|^/sub/method$|',
        })
    self.assertResponse(self.send(root, '/desc'), 200, '''\
/
└── sub/
    └── method    # This method outputs a JSON list.
''')

  #----------------------------------------------------------------------------
  def test_exclude(self):
    'Setting the Describer `exclude` parameter is inclusive'
    root = SimpleRoot()
    root.desc = DescribeController(
      root, doc='URL tree description.',
      settings={
        'formats': 'txt',
        'index-redirect': 'false',
        'exclude': ('|^/sub/method$|', '|^/desc(/.*)?$|'),
        })
    self.assertResponse(self.send(root, '/desc'), 200, '''\
/                   # The default root.
├── rest            # A RESTful entry.
│   ├── <DELETE>    # Deletes the entry.
│   ├── <GET>       # Gets the current value.
│   ├── <POST>      # Creates a new entry.
│   └── <PUT>       # Updates the value.
├── swi             # A sub-controller providing only an index.
└── unknown/?       # A dynamically generated sub-controller.
''')

  #----------------------------------------------------------------------------
  def test_request_option_control_default(self):
    'By default, no request options are honored during rendering'
    root = SimpleRoot()
    root.desc = DescribeController(
      root, doc='URL tree description.',
      settings={
        'formats': 'txt',
        'index-redirect': 'false',
        'exclude': ('|^/sub/method$|',
                    '|^/desc(/.*)?$|'),
        })
    self.assertResponse(self.send(root, '/desc?format=html&showRest=false&showInfo=false'), 200, '''\
/                   # The default root.
├── rest            # A RESTful entry.
│   ├── <DELETE>    # Deletes the entry.
│   ├── <GET>       # Gets the current value.
│   ├── <POST>      # Creates a new entry.
│   └── <PUT>       # Updates the value.
├── swi             # A sub-controller providing only an index.
└── unknown/?       # A dynamically generated sub-controller.
''')

  #----------------------------------------------------------------------------
  def test_request_option_control_enable_all(self):
    'The rendering options pulled from the request parameters can be set to all options'
    root = SimpleRoot()
    root.desc = DescribeController(
      root, doc='URL tree description.',
      settings={
        'formats': 'txt',
        'index-redirect': 'false',
        'exclude': ('|^/sub/method$|', '|^/desc(/.*)?$|'),
        'format.request': 'true',
        })
    self.assertResponse(self.send(root, '/desc?showRest=false&showInfo=false'), 200, '''\
/
├── rest
├── swi
└── unknown/?
''')
    self.assertIn('<html', self.send(root, '/desc?format=html&showRest=false&showInfo=false').body)

  #----------------------------------------------------------------------------
  def test_request_option_control_enable_list(self):
    'The rendering options pulled from the request parameters can be a list of specific options'
    root = SimpleRoot()
    root.desc = DescribeController(
      root, doc='URL tree description.',
      settings={
        'formats': 'txt',
        'index-redirect': 'false',
        'exclude': ('|^/sub/method$|', '|^/desc(/.*)?$|'),
        'format.request': 'format showInfo',
        })
    self.assertResponse(self.send(root, '/desc?showRest=false&showInfo=false'), 200, '''\
/
├── rest
│   ├── <DELETE>
│   ├── <GET>
│   ├── <POST>
│   └── <PUT>
├── swi
└── unknown/?
''')
    self.assertIn('<html', self.send(root, '/desc?format=html&showRest=false&showInfo=false').body)

  #----------------------------------------------------------------------------
  def test_mixed_restful_and_dispatch_txt(self):
    'The Describer supports mixing RESTful and URL component methods in "txt" format'
    class Access(Controller):
      @index
      def index(self, request):
        'Access control'
    class Rest(RestController):
      'RESTful access, with sub-component'
      access = Access()
      @expose
      def put(self, request):
        'Modify this object'
        pass
      @expose
      def groups(self, request):
        'Return the groups for this object'
    class Root(Controller):
      rest = Rest()
    root = Root()
    root.desc = DescribeController(
      root, doc='URL tree description.',
      settings={
        'formats': 'txt',
        'index-redirect': 'false',
        'exclude': '|^/desc(/.*)?$|',
        })
    self.assertResponse(self.send(root, '/desc'), 200, '''\
/
└── rest/         # RESTful access, with sub-component
    ├── <PUT>     # Modify this object
    ├── access    # Access control
    └── groups    # Return the groups for this object
''')

  #----------------------------------------------------------------------------
  def test_format_rst_standard(self):
    'The Describer can render a reStructuredText description'
    root = SimpleRoot()
    root.desc = DescribeController(
      root, doc='URL tree description.',
      settings={
        'exclude': '|^/desc/.*|',
        'index-redirect': 'false',
        'format.default': 'rst',
        'format.default.showImpl': 'true',
        'entries.filters': docsEnhancer,
        })
    self.assertResponse(self.send(root, '/desc'), 200, '''\
===============
Contents of "/"
===============

/
=

Handler: pyramid_describe.test.SimpleRoot() [instance]

The default root.

/desc
=====

Handler: pyramid_describe.controller.DescribeController() [instance]

URL tree description.

/rest
=====

Handler: pyramid_describe.test.Rest() [instance]

A RESTful entry.

Methods
-------

**DELETE**
``````````

Handler: pyramid_describe.test.Rest().delete [method]

Deletes the entry.

**GET**
```````

Handler: pyramid_describe.test.Rest().get [method]

Gets the current value.

**POST**
````````

Handler: pyramid_describe.test.Rest().post [method]

Creates a new entry.

Parameters
::::::::::

**size**
\'''\'''\''

int, optional, default 4096

The anticipated maximum size

**text**
\'''\'''\''

str

The text content for the posting

Returns
:::::::

**str**
\'''\'''\'

The ID of the new posting

Raises
::::::

**HTTPUnauthorized**
\'''\'''\'''\'''\'''\'''\''

Authenticated access is required

**HTTPForbidden**
\'''\'''\'''\'''\'''\''

The user does not have posting privileges

**PUT**
```````

Handler: pyramid_describe.test.Rest().put [method]

Updates the value.

/sub/method
===========

Handler: pyramid_describe.test.Sub().method [method]

This method outputs a JSON list.

/swi
====

Handler: pyramid_describe.test.SubIndex() [instance]

A sub-controller providing only an index.

/unknown/?
==========

Handler: pyramid_describe.test.Unknown [class]

A dynamically generated sub-controller.

======
Legend
======

`{{NAME}}`
========

Placeholder -- usually replaced with an ID or other identifier of a RESTful
object.

`<NAME>`
========

Not an actual endpoint, but the HTTP method to use.

`NAME/?`
========

Dynamically evaluated endpoint; no further information can be determined
without request-specific details.

`*`
===

This endpoint is a `default` handler, and is therefore free to interpret path
arguments dynamically; no further information can be determined without
request-specific details.

`...`
=====

This endpoint is a `lookup` handler, and is therefore free to interpret path
arguments dynamically; no further information can be determined without
request-specific details.

.. meta::
  :title: Contents of "/"
  :generator: pyramid-describe/{version} [format=rst]
  :location: http://localhost/desc
'''.format(version=getVersion('pyramid_describe')))

  #----------------------------------------------------------------------------
  def test_format_rst_title(self):
    'The Describer can change the reStructuredText title based on options'
    root = SimpleRoot()
    root.desc = DescribeController(
      root, doc='URL tree description.',
      settings={
        'include': '|^/swi|',
        'index-redirect': 'false',
        'format.default': 'rst',
        'format.default.title': 'Application API Details',
        'format.default.showImpl': 'true',
        'entries.filters': docsEnhancer,
        })
    self.assertResponse(self.send(root, '/desc'), 200, '''\
=======================
Application API Details
=======================

/swi
====

Handler: pyramid_describe.test.SubIndex() [instance]

A sub-controller providing only an index.

======
Legend
======

`{{NAME}}`
========

Placeholder -- usually replaced with an ID or other identifier of a RESTful
object.

`<NAME>`
========

Not an actual endpoint, but the HTTP method to use.

`NAME/?`
========

Dynamically evaluated endpoint; no further information can be determined
without request-specific details.

`*`
===

This endpoint is a `default` handler, and is therefore free to interpret path
arguments dynamically; no further information can be determined without
request-specific details.

`...`
=====

This endpoint is a `lookup` handler, and is therefore free to interpret path
arguments dynamically; no further information can be determined without
request-specific details.

.. meta::
  :title: Application API Details
  :generator: pyramid-describe/{version} [format=rst]
  :location: http://localhost/desc
'''.format(version=getVersion('pyramid_describe')))

  #----------------------------------------------------------------------------
  def test_format_rst_maximum(self):
    'The Describer renders reStructuredText with maximum decorations'
    root = SimpleRoot()
    root.desc = DescribeController(
      root, doc='URL tree description.',
      settings={
        'exclude': '|^/desc/.*|',
        'index-redirect': 'false',
        'format.default': 'rst',
        'format.default.showImpl': 'true',
        'format.default.rstMax': 'true',
        'entries.filters': docsEnhancer,
        })
    self.assertResponse(self.send(root, '/desc'), 200, '''\
.. title:: Contents of "/"

.. class:: endpoints
.. id:: section-endpoints

===============
Contents of "/"
===============

.. class:: endpoint
.. id:: endpoint-_2F

/
=

.. class:: handler
.. id:: handler-endpoint-_2F

Handler: pyramid_describe.test.SimpleRoot() [instance]

The default root.

.. class:: endpoint
.. id:: endpoint-_2Fdesc

/desc
=====

.. class:: handler
.. id:: handler-endpoint-_2Fdesc

Handler: pyramid_describe.controller.DescribeController() [instance]

URL tree description.

.. class:: endpoint
.. id:: endpoint-_2Frest

/rest
=====

.. class:: handler
.. id:: handler-endpoint-_2Frest

Handler: pyramid_describe.test.Rest() [instance]

A RESTful entry.

.. class:: methods
.. id:: methods-endpoint-_2Frest

Methods
-------

.. class:: method
.. id:: method-_2Frest-DELETE

**DELETE**
``````````

.. class:: handler
.. id:: handler-method-_2Frest-DELETE

Handler: pyramid_describe.test.Rest().delete [method]

Deletes the entry.

.. class:: method
.. id:: method-_2Frest-GET

**GET**
```````

.. class:: handler
.. id:: handler-method-_2Frest-GET

Handler: pyramid_describe.test.Rest().get [method]

Gets the current value.

.. class:: method post-is-not-put fake-docs-here
.. id:: method-_2Frest-POST

**POST**
````````

.. class:: handler
.. id:: handler-method-_2Frest-POST

Handler: pyramid_describe.test.Rest().post [method]

Creates a new entry.

.. class:: params
.. id:: params-method-_2Frest-POST

Parameters
::::::::::

.. class:: param
.. id:: param-method-_2Frest-POST-size

**size**
\'''\'''\''

.. class:: spec

int, optional, default 4096

The anticipated maximum size

.. class:: param
.. id:: param-method-_2Frest-POST-text

**text**
\'''\'''\''

.. class:: spec

str

The text content for the posting

.. class:: returns
.. id:: returns-method-_2Frest-POST

Returns
:::::::

.. class:: return
.. id:: return-method-_2Frest-POST-str

**str**
\'''\'''\'

The ID of the new posting

.. class:: raises
.. id:: raises-method-_2Frest-POST

Raises
::::::

.. class:: raise
.. id:: raise-method-_2Frest-POST-HTTPUnauthorized

**HTTPUnauthorized**
\'''\'''\'''\'''\'''\'''\''

Authenticated access is required

.. class:: raise
.. id:: raise-method-_2Frest-POST-HTTPForbidden

**HTTPForbidden**
\'''\'''\'''\'''\'''\''

The user does not have posting privileges

.. class:: method
.. id:: method-_2Frest-PUT

**PUT**
```````

.. class:: handler
.. id:: handler-method-_2Frest-PUT

Handler: pyramid_describe.test.Rest().put [method]

Updates the value.

.. class:: endpoint
.. id:: endpoint-_2Fsub_2Fmethod

/sub/method
===========

.. class:: handler
.. id:: handler-endpoint-_2Fsub_2Fmethod

Handler: pyramid_describe.test.Sub().method [method]

This method outputs a JSON list.

.. class:: endpoint sub-with-index
.. id:: endpoint-_2Fswi

/swi
====

.. class:: handler
.. id:: handler-endpoint-_2Fswi

Handler: pyramid_describe.test.SubIndex() [instance]

A sub-controller providing only an index.

.. class:: endpoint
.. id:: endpoint-_2Funknown

/unknown/?
==========

.. class:: handler
.. id:: handler-endpoint-_2Funknown

Handler: pyramid_describe.test.Unknown [class]

A dynamically generated sub-controller.

.. class:: legend
.. id:: section-legend

======
Legend
======

.. class:: legend-item
.. id:: legend-item-_7BNAME_7D

`{{NAME}}`
========

Placeholder -- usually replaced with an ID or other identifier of a RESTful
object.

.. class:: legend-item
.. id:: legend-item-_3CNAME_3E

`<NAME>`
========

Not an actual endpoint, but the HTTP method to use.

.. class:: legend-item
.. id:: legend-item-NAME_2F_3F

`NAME/?`
========

Dynamically evaluated endpoint; no further information can be determined
without request-specific details.

.. class:: legend-item
.. id:: legend-item-_2A

`*`
===

This endpoint is a `default` handler, and is therefore free to interpret path
arguments dynamically; no further information can be determined without
request-specific details.

.. class:: legend-item
.. id:: legend-item-_2E_2E_2E

`...`
=====

This endpoint is a `lookup` handler, and is therefore free to interpret path
arguments dynamically; no further information can be determined without
request-specific details.

.. meta::
  :title: Contents of "/"
  :generator: pyramid-describe/{version} [format=rst]
  :location: http://localhost/desc
  :pdfkit-page-size: A4
  :pdfkit-orientation: Portrait
  :pdfkit-margin-top: 10mm
  :pdfkit-margin-right: 10mm
  :pdfkit-margin-bottom: 10mm
  :pdfkit-margin-left: 10mm
'''.format(version=getVersion('pyramid_describe')))

  #----------------------------------------------------------------------------
  def test_mixed_restful_and_dispatch_rst(self):
    'The Describer supports mixing RESTful and URL component methods in "rst" format'
    class Access(Controller):
      @index
      def index(self, request):
        'Access control'
    class Rest(RestController):
      'RESTful access, with sub-component'
      access = Access()
      @expose
      def put(self, request):
        'Modify this object'
        pass
      @expose
      def groups(self, request):
        'Return the groups for this object'
    class Root(Controller):
      rest = Rest()
    root = Root()
    root.desc = DescribeController(
      root, doc='URL tree description.',
      settings=settings_minRst)
    self.assertResponse(self.send(root, '/desc'), 200, '''\
===============
Contents of "/"
===============

/rest
=====

RESTful access, with sub-component

Methods
-------

**PUT**
```````

Modify this object

/rest/access
============

Access control

/rest/groups
============

Return the groups for this object
''')

#   # TODO: enable this when txt is sensitive to forceSlash...
#   #----------------------------------------------------------------------------
#   def test_format_txt_differentiates_forced_slash_index(self):
#     'The Describer can differentiate a forced-slash index'
#     class SubIndexForceSlash(Controller):
#       @index
#       def myindex(self, request):
#         'A sub-controller providing only a slash-index.'
#         return 'my.index'
#     root = SimpleRoot()
#     root.swfs = SubIndexForceSlash()
#     root.desc = DescribeController(root, doc='URL tree description.')
#     self.assertResponse(self.send(root, '/desc'), 200, '''\
# /
# ├── desc
# ├── sub/
# │   └── method
# ├── swfs/
# └── swi
# ''')

  #----------------------------------------------------------------------------
  def test_prune_index(self):
    'The Describer can collapse up index docs'
    class Root(Controller):
      'The Root'
      @index
      def method(self, request):
        'The index method'
        return 'ok.index'
    root = Root()
    root.desc = DescribeController(
      root, doc='URL tree description.',
       settings=settings_minRst)
    self.assertResponse(self.send(root, '/desc'), 200, '''\
===============
Contents of "/"
===============

/
=

The index method
''')

  #----------------------------------------------------------------------------
  def test_format_html(self):
    'The Describer can render HTML'
    root = SimpleRoot()
    root.desc = DescribeController(
      root, doc='URL tree description.',
      settings={
        'exclude': '|^/desc/.*$|',
        'index-redirect': 'false',
        'entries.filters': docsEnhancer,
        'format.default.title': 'Application API',
        'format.default.rstMax': 'true',
        })
    res = self.send(root, '/desc')
    chk = '''\
<?xml version="1.0" encoding="UTF-8" ?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
 <head>
  <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
  <meta name="generator" content="Docutils 0.10: http://docutils.sourceforge.net/" />
  <title>Application API</title>
  <meta content="Application API" name="title" />
  <meta content="pyramid-describe/{version} [format=html]" name="generator" />
  <meta content="http://localhost/desc" name="location" />
  <meta content="A4" name="pdfkit-page-size" />
  <meta content="Portrait" name="pdfkit-orientation" />
  <meta content="10mm" name="pdfkit-margin-top" />
  <meta content="10mm" name="pdfkit-margin-right" />
  <meta content="10mm" name="pdfkit-margin-bottom" />
  <meta content="10mm" name="pdfkit-margin-left" />
  <style type="text/css">

body {{
  padding: 2em;
}}

#section-endpoints > h1 {{
  margin-top: 0;
}}

.section > * {{
  margin-left: 30px;
}}

.section > h1,
.section > h2,
.section > h3,
.section > h4,
.section > h5,
.section > h6 {{
  margin-left: 0;
}}

#section-legend {{
  font-size: 70%;
  margin-top: 5em;
  border-top: 2px solid #e0e0e0;
}}

</style>
 </head>
 <body>
  <div class="document">
   <div class="endpoints section" id="section-endpoints">
    <h1>Application API</h1>
    <div class="endpoint section" id="endpoint-_2F">
     <h2>/</h2>
     <p>The default root.</p>
    </div>
    <div class="endpoint section" id="endpoint-_2Fdesc">
     <h2>/desc</h2>
     <p>URL tree description.</p>
    </div>
    <div class="endpoint section" id="endpoint-_2Frest">
     <h2>/rest</h2>
     <p>A RESTful entry.</p>
     <div class="methods section" id="methods-endpoint-_2Frest">
      <h3>Methods</h3>
      <div class="method section" id="method-_2Frest-DELETE">
       <h4>
        <strong>DELETE</strong>
       </h4>
       <p>Deletes the entry.</p>
      </div>
      <div class="method section" id="method-_2Frest-GET">
       <h4>
        <strong>GET</strong>
       </h4>
       <p>Gets the current value.</p>
      </div>
      <div class="method post-is-not-put fake-docs-here section" id="method-_2Frest-POST">
       <h4>
        <strong>POST</strong>
       </h4>
       <p>Creates a new entry.</p>
       <div class="params section" id="params-method-_2Frest-POST">
        <h5>Parameters</h5>
        <div class="param section" id="param-method-_2Frest-POST-size">
         <h6>
          <strong>size</strong>
         </h6>
         <p class="spec">int, optional, default 4096</p>
         <p>The anticipated maximum size</p>
        </div>
        <div class="param section" id="param-method-_2Frest-POST-text">
         <h6>
          <strong>text</strong>
         </h6>
         <p class="spec">str</p>
         <p>The text content for the posting</p>
        </div>
       </div>
       <div class="returns section" id="returns-method-_2Frest-POST">
        <h5>Returns</h5>
        <div class="return section" id="return-method-_2Frest-POST-str">
         <h6>
          <strong>str</strong>
         </h6>
         <p>The ID of the new posting</p>
        </div>
       </div>
       <div class="raises section" id="raises-method-_2Frest-POST">
        <h5>Raises</h5>
        <div class="raise section" id="raise-method-_2Frest-POST-HTTPUnauthorized">
         <h6>
          <strong>HTTPUnauthorized</strong>
         </h6>
         <p>Authenticated access is required</p>
        </div>
        <div class="raise section" id="raise-method-_2Frest-POST-HTTPForbidden">
         <h6>
          <strong>HTTPForbidden</strong>
         </h6>
         <p>The user does not have posting privileges</p>
        </div>
       </div>
      </div>
      <div class="method section" id="method-_2Frest-PUT">
       <h4>
        <strong>PUT</strong>
       </h4>
       <p>Updates the value.</p>
      </div>
     </div>
    </div>
    <div class="endpoint section" id="endpoint-_2Fsub_2Fmethod">
     <h2>/sub/method</h2>
     <p>This method outputs a JSON list.</p>
    </div>
    <div class="endpoint sub-with-index section" id="endpoint-_2Fswi">
     <h2>/swi</h2>
     <p>A sub-controller providing only an index.</p>
    </div>
    <div class="endpoint section" id="endpoint-_2Funknown">
     <h2>/unknown/?</h2>
     <p>A dynamically generated sub-controller.</p>
    </div>
   </div>
   <div class="legend section" id="section-legend">
    <h1>Legend</h1>
    <div class="legend-item section" id="legend-item-_7BNAME_7D">
     <h2>
      <cite>{{NAME}}</cite>
     </h2>
     <p>Placeholder -- usually replaced with an ID or other identifier of a RESTful
object.</p>
    </div>
    <div class="legend-item section" id="legend-item-_3CNAME_3E">
     <h2>
      <cite>&lt;NAME&gt;</cite>
     </h2>
     <p>Not an actual endpoint, but the HTTP method to use.</p>
    </div>
    <div class="legend-item section" id="legend-item-NAME_2F_3F">
     <h2>
      <cite>NAME/?</cite>
     </h2>
     <p>Dynamically evaluated endpoint; no further information can be determined
without request-specific details.</p>
    </div>
    <div class="legend-item section" id="legend-item-_2A">
     <h2>
      <cite>*</cite>
     </h2>
     <p>This endpoint is a <cite>default</cite> handler, and is therefore free to interpret path
arguments dynamically; no further information can be determined without
request-specific details.</p>
    </div>
    <div class="legend-item section" id="legend-item-_2E_2E_2E">
     <h2>
      <cite>...</cite>
     </h2>
     <p>This endpoint is a <cite>lookup</cite> handler, and is therefore free to interpret path
arguments dynamically; no further information can be determined without
request-specific details.</p>
    </div>
   </div>
  </div>
 </body>
</html>
'''.format(version=getVersion('pyramid_describe'))

    chk = re.sub('>\s*<', '><', chk, flags=re.MULTILINE)
    res.body = re.sub('>\s*<', '><', res.body, flags=re.MULTILINE)
    self.assertResponse(res, 200, chk, xml=True)

  #----------------------------------------------------------------------------
  def test_format_html_filters(self):
    'The Describer honors the format-specific `filters` option'
    def remove_body(parts, options):
      parts['body'] = ''
      return parts
    root = SimpleRoot()
    root.desc = DescribeController(
      root, doc='URL tree description.',
      settings={
        'entries.filters': docsEnhancer,
        'index-redirect': 'false',
        'exclude': '|^/desc/.*$|',
        'format.default.showLegend': 'false',
        'format.default.rstPdfkit': 'false',
        'format.html.default.cssPath': None,
        'format.html.default.filters': remove_body,
        })
    res = self.send(root, '/desc')
    chk = '''\
<?xml version="1.0" encoding="UTF-8" ?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
 <head>
  <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
  <meta name="generator" content="Docutils 0.10: http://docutils.sourceforge.net/" />
  <title>Contents of &quot;/&quot;</title>
  <meta content="Contents of &quot;/&quot;" name="title" />
  <meta content="pyramid-describe/{version} [format=html]" name="generator" />
  <meta content="http://localhost/desc" name="location" />
 </head>
 <body>
  <div class="endpoints document" id="section-endpoints">
   <h1 class="title">Contents of &quot;/&quot;</h1>
  </div>
 </body>
</html>
'''.format(version=getVersion('pyramid_describe'))

    chk = re.sub('>\s*<', '><', chk, flags=re.MULTILINE)
    res.body = re.sub('>\s*<', '><', res.body, flags=re.MULTILINE)
    self.assertResponse(res, 200, chk, xml=True)

  #----------------------------------------------------------------------------
  def test_format_json(self):
    'The Describer can render JSON'
    root = SimpleRoot()
    root.desc = DescribeController(
       root, doc='URL tree description.',
       settings={
        'format.default': 'json',
        'index-redirect': 'false',
        'entries.filters': docsEnhancer,
        'exclude': '|^/desc/.*|',
        })
    res = self.send(root, '/desc')
    chk = '''{
  "application": {
    "url": "http://localhost",
    "endpoints": [
      { "name": "",
        "id": "endpoint-_2F",
        "path": "/",
        "decoratedName": "",
        "decoratedPath": "/",
        "doc": "The default root."
      },
      { "name": "desc",
        "id": "endpoint-_2Fdesc",
        "path": "/desc",
        "decoratedName": "desc",
        "decoratedPath": "/desc",
        "doc": "URL tree description."
      },
      { "name": "rest",
        "id": "endpoint-_2Frest",
        "path": "/rest",
        "decoratedName": "rest",
        "decoratedPath": "/rest",
        "doc": "A RESTful entry.",
        "methods": [
          { "name": "DELETE",
            "id": "method-_2Frest-DELETE",
            "doc": "Deletes the entry."
          },
          { "name": "GET",
            "id": "method-_2Frest-GET",
            "doc": "Gets the current value."
          },
          { "name": "POST",
            "id": "method-_2Frest-POST",
            "doc": "Creates a new entry.",
            "params": [
              { "name": "size",
                "id": "param-_2Frest_3F_5Fmethod_3DPOST-size",
                "type": "int",
                "optional": true,
                "default": 4096,
                "doc": "The anticipated maximum size"
              },
              { "name": "text",
                "id": "param-_2Frest_3F_5Fmethod_3DPOST-text",
                "type": "str",
                "optional": false,
                "doc": "The text content for the posting"
              }
            ],
            "returns": [
              { "type": "str",
                "id": "return-_2Frest_3F_5Fmethod_3DPOST-0-str",
                "doc": "The ID of the new posting"
              }
            ],
            "raises": [
              { "type": "HTTPUnauthorized",
                "id": "raise-_2Frest_3F_5Fmethod_3DPOST-0-HTTPUnauthorized",
                "doc": "Authenticated access is required"
              },
              { "type": "HTTPForbidden",
                "id": "raise-_2Frest_3F_5Fmethod_3DPOST-1-HTTPForbidden",
                "doc": "The user does not have posting privileges"
              }
            ]
          },
          { "name": "PUT",
            "id": "method-_2Frest-PUT",
            "doc": "Updates the value."
          }
        ]
      },
      { "name": "method",
        "id": "endpoint-_2Fsub_2Fmethod",
        "path": "/sub/method",
        "decoratedName": "method",
        "decoratedPath": "/sub/method",
        "doc": "This method outputs a JSON list."
      },
      { "name": "swi",
        "id": "endpoint-_2Fswi",
        "path": "/swi",
        "decoratedName": "swi",
        "decoratedPath": "/swi",
        "doc": "A sub-controller providing only an index."
      },
      { "name": "unknown",
        "id": "endpoint-_2Funknown",
        "path": "/unknown",
        "decoratedName": "unknown/?",
        "decoratedPath": "/unknown/?",
        "doc": "A dynamically generated sub-controller."
      }
    ]
  }
}
'''
    chk = json.dumps(json.loads(chk), sort_keys=True, indent=4)
    res.body = json.dumps(json.loads(res.body), sort_keys=True, indent=4)
    self.assertResponse(res, 200, chk)

  #----------------------------------------------------------------------------
  def test_format_yaml(self):
    'The Describer can render YAML'
    try:
      import yaml
    except ImportError:
      sys.stderr.write('*** YAML LIBRARY NOT PRESENT - SKIPPING *** ')
      return
    root = SimpleRoot()
    root.desc = DescribeController(
       root, doc='URL tree description.',
       settings={
        'format.default': 'yaml',
        'index-redirect': 'false',
        'entries.filters': docsEnhancer,
        'exclude': '|^/desc/.*|',
        })
    res = self.send(root, '/desc')
    chk = '''
application:
  url: 'http://localhost'
  endpoints:
    - name: ''
      id: 'endpoint-_2F'
      path: /
      decoratedName: ''
      decoratedPath: /
      doc: The default root.
    - name: desc
      id: 'endpoint-_2Fdesc'
      path: /desc
      decoratedName: desc
      decoratedPath: /desc
      doc: URL tree description.
    - name: rest
      id: 'endpoint-_2Frest'
      path: /rest
      decoratedName: rest
      decoratedPath: /rest
      doc: A RESTful entry.
      methods:
        - name: DELETE
          id: 'method-_2Frest-DELETE'
          doc: Deletes the entry.
        - name: GET
          id: 'method-_2Frest-GET'
          doc: Gets the current value.
        - name: POST
          id: 'method-_2Frest-POST'
          doc: Creates a new entry.
          params:
            - name: size
              id: 'param-_2Frest_3F_5Fmethod_3DPOST-size'
              type: int
              optional: true
              default: 4096
              doc: The anticipated maximum size
            - name: text
              id: 'param-_2Frest_3F_5Fmethod_3DPOST-text'
              type: str
              optional: false
              doc: The text content for the posting
          returns:
            - type: str
              id: 'return-_2Frest_3F_5Fmethod_3DPOST-0-str'
              doc: The ID of the new posting
          raises:
            - type: HTTPUnauthorized
              id: 'raise-_2Frest_3F_5Fmethod_3DPOST-0-HTTPUnauthorized'
              doc: Authenticated access is required
            - type: HTTPForbidden
              id: 'raise-_2Frest_3F_5Fmethod_3DPOST-1-HTTPForbidden'
              doc: The user does not have posting privileges
        - name: PUT
          id: 'method-_2Frest-PUT'
          doc: Updates the value.
    - name: method
      id: 'endpoint-_2Fsub_2Fmethod'
      path: /sub/method
      decoratedName: method
      decoratedPath: /sub/method
      doc: This method outputs a JSON list.
    - name: swi
      id: 'endpoint-_2Fswi'
      path: /swi
      decoratedName: swi
      decoratedPath: /swi
      doc: A sub-controller providing only an index.
    - name: unknown
      id: 'endpoint-_2Funknown'
      path: /unknown
      decoratedName: unknown/?
      decoratedPath: /unknown/?
      doc: A dynamically generated sub-controller.
'''
    import yaml
    chk = yaml.dump(yaml.load(chk), default_flow_style=False)
    res.body = yaml.dump(yaml.load(res.body), default_flow_style=False)
    self.assertResponse(res, 200, chk)

  #----------------------------------------------------------------------------
  def test_format_yaml_dedent(self):
    'The Describer renders YAML with dedented documentation'
    try:
      import yaml
    except ImportError:
      sys.stderr.write('*** YAML LIBRARY NOT PRESENT - SKIPPING *** ')
      return
    class Root(Controller):
      @expose
      def describe(self, request):
        '''
        A multi-line
        comment.
        '''
        pass
    root = Root()
    root.desc = DescribeController(
       root, doc='URL tree description.',
       settings={
        'format.default': 'yaml',
        'index-redirect': 'false',
        'entries.filters': docsEnhancer,
        'exclude': '|^/desc/.*|',
        })
    res = self.send(root, '/desc')
    chk = '''
application:
  url: http://localhost
  endpoints:
    - name: desc
      id: 'endpoint-_2Fdesc'
      path: /desc
      decoratedName: desc
      decoratedPath: /desc
      doc: URL tree description.
    - name: describe
      id: 'endpoint-_2Fdescribe'
      path: /describe
      decoratedName: describe
      decoratedPath: /describe
      doc: "A multi-line\\ncomment."
'''
    self.assertEqual(yaml.load(res.body), yaml.load(chk))

  #----------------------------------------------------------------------------
  def test_format_xml(self):
    'The Describer can render XML'
    root = SimpleRoot()
    root.desc = DescribeController(
      root, doc='URL tree description.',
      settings={
        'format.default': 'xml',
        'index-redirect': 'false',
        'entries.filters': docsEnhancer,
        'exclude': '|^/desc/.*|',
        })
    res = self.send(root, '/desc')
    chk = '''\
<?xml version="1.0" encoding="UTF-8"?>
<application url="http://localhost">
 <endpoint name="" path="/" decorated-name="" decorated-path="/" id="endpoint-_2F">
  <doc>The default root.</doc>
 </endpoint>
 <endpoint name="desc" path="/desc" decorated-name="desc" decorated-path="/desc" id="endpoint-_2Fdesc">
  <doc>URL tree description.</doc>
 </endpoint>
 <endpoint name="rest" path="/rest" decorated-name="rest" decorated-path="/rest" id="endpoint-_2Frest">
  <doc>A RESTful entry.</doc>
  <method id="method-_2Frest-DELETE" name="DELETE"><doc>Deletes the entry.</doc></method>
  <method id="method-_2Frest-GET" name="GET"><doc>Gets the current value.</doc></method>
  <method id="method-_2Frest-POST" name="POST">
   <doc>Creates a new entry.</doc>
   <param default="4096" id="param-_2Frest_3F_5Fmethod_3DPOST-size" name="size" optional="True" type="int">
    <doc>The anticipated maximum size</doc>
   </param>
   <param id="param-_2Frest_3F_5Fmethod_3DPOST-text" name="text" optional="False" type="str">
    <doc>The text content for the posting</doc>
   </param>
   <return id="return-_2Frest_3F_5Fmethod_3DPOST-0-str" type="str">
    <doc>The ID of the new posting</doc>
   </return>
   <raise id="raise-_2Frest_3F_5Fmethod_3DPOST-0-HTTPUnauthorized" type="HTTPUnauthorized">
    <doc>Authenticated access is required</doc>
   </raise>
   <raise id="raise-_2Frest_3F_5Fmethod_3DPOST-1-HTTPForbidden" type="HTTPForbidden">
    <doc>The user does not have posting privileges</doc>
   </raise>
  </method>
  <method id="method-_2Frest-PUT" name="PUT"><doc>Updates the value.</doc></method>
 </endpoint>
 <endpoint name="method" path="/sub/method" decorated-name="method" decorated-path="/sub/method" id="endpoint-_2Fsub_2Fmethod">
  <doc>This method outputs a JSON list.</doc>
 </endpoint>
 <endpoint name="swi" path="/swi" decorated-name="swi" decorated-path="/swi" id="endpoint-_2Fswi">
  <doc>A sub-controller providing only an index.</doc>
 </endpoint>
 <endpoint name="unknown" path="/unknown" decorated-name="unknown/?" decorated-path="/unknown/?" id="endpoint-_2Funknown">
  <doc>A dynamically generated sub-controller.</doc>
 </endpoint>
</application>
'''
    chk = ET.tostring(ET.fromstring(re.sub('>\s*<', '><', chk, flags=re.MULTILINE)), 'UTF-8')
    chk = '<?xml version="1.0" encoding="UTF-8"?>\n' + chk[chk.find('<application'):]
    self.assertResponse(res, 200, chk, xml=True)
    self.assertTrue(res.body.startswith('<?xml version="1.0" encoding="UTF-8"?>'))

  #----------------------------------------------------------------------------
  def test_format_wadl(self):
    'The Describer can render WADL'
    root = SimpleRoot()
    root.desc = DescribeController(
       root, doc='URL tree description.',
       settings={
        'format.default': 'wadl',
        'index-redirect': 'false',
        'entries.filters': docsEnhancer,
        'exclude': '|^/desc/.*|',
        })
    res = self.send(root, '/desc')
    chk = '''
<application
 xmlns="http://research.sun.com/wadl/2006/10"
 xmlns:xsd="http://www.w3.org/2001/XMLSchema"
 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
 xmlns:pd="http://pythonhosted.org/pyramid_describer/xmlns/0.1/doc"
 xsi:schemaLocation="http://research.sun.com/wadl/2006/10 wadl.xsd"
 >
 <resources base="http://localhost">
  <resource id="endpoint-_2F" path="">
   <pd:doc>The default root.</pd:doc>
   <method id="method-_2F-GET" name="GET"/>
  </resource>
  <resource id="endpoint-_2Fdesc" path="desc">
   <pd:doc>URL tree description.</pd:doc>
   <method id="method-_2Fdesc-GET" name="GET"/>
  </resource>
  <resource id="endpoint-_2Frest" path="rest">
   <pd:doc>A RESTful entry.</pd:doc>
   <method id="method-_2Frest-DELETE" name="DELETE">
    <pd:doc>Deletes the entry.</pd:doc>
   </method>
   <method id="method-_2Frest-GET" name="GET">
    <pd:doc>Gets the current value.</pd:doc>
   </method>
   <method id="method-_2Frest-POST" name="POST">
    <pd:doc>Creates a new entry.</pd:doc>
    <request>
     <param id="param-_2Frest_3F_5Fmethod_3DPOST-size" name="size" type="xsd:integer" required="false" default="4096">
      <pd:doc>The anticipated maximum size</pd:doc>
     </param>
     <param id="param-_2Frest_3F_5Fmethod_3DPOST-text" name="text" type="xsd:string" required="true">
      <pd:doc>The text content for the posting</pd:doc>
     </param>
    </request>
    <response>
     <representation id="return-_2Frest_3F_5Fmethod_3DPOST-0-str" element="xsd:string">
      <pd:doc>The ID of the new posting</pd:doc>
     </representation>
     <fault id="raise-_2Frest_3F_5Fmethod_3DPOST-0-HTTPUnauthorized" element="HTTPUnauthorized">
      <pd:doc>Authenticated access is required</pd:doc>
     </fault>
     <fault id="raise-_2Frest_3F_5Fmethod_3DPOST-1-HTTPForbidden" element="HTTPForbidden">
      <pd:doc>The user does not have posting privileges</pd:doc>
     </fault>
    </response>
   </method>
   <method id="method-_2Frest-PUT" name="PUT">
    <pd:doc>Updates the value.</pd:doc>
   </method>
  </resource>
  <resource id="endpoint-_2Fsub_2Fmethod" path="sub/method">
   <pd:doc>This method outputs a JSON list.</pd:doc>
   <method id="method-_2Fsub_2Fmethod-GET" name="GET"/>
  </resource>
  <resource id="endpoint-_2Fswi" path="swi">
   <pd:doc>A sub-controller providing only an index.</pd:doc>
   <method id="method-_2Fswi-GET" name="GET"/>
  </resource>
  <resource id="endpoint-_2Funknown" path="unknown">
   <pd:doc>A dynamically generated sub-controller.</pd:doc>
   <method id="method-_2Funknown-GET" name="GET"/>
  </resource>
 </resources>
</application>
'''
    # todo: what to do about mediaType, status, and namespaces?...
    # <representation mediaType="application/xml" element="yn:ResultSet"/>
    # <fault status="400" mediaType="application/xml" element="ya:Error"/>
    def roundtrip(xml):
      return ET.tostring(ET.fromstring(xml), 'UTF-8')
    chk = ET.tostring(ET.fromstring(re.sub('>\s*<', '><', chk, flags=re.MULTILINE)), 'UTF-8')
    res.body = roundtrip(res.body)
    self.assertResponse(res, 200, chk, xml=True)

  #----------------------------------------------------------------------------
  def test_format_pdf(self):
    'The Describer can render PDF'
    try:
      import pdfkit
    except ImportError:
      sys.stderr.write('*** PDFKIT LIBRARY NOT PRESENT - SKIPPING *** ')
      return
    root = SimpleRoot()
    root.desc = DescribeController(
       root, doc='URL tree description.',
       settings={
         'format.default': 'pdf',
         'index-redirect': 'false',
         'entries.filters': docsEnhancer,
         'exclude': '|^/desc/.*|',
         })
    res = self.send(root, '/desc')
    # todo: check content-type...
    self.assertTrue(res.body.startswith('%PDF-1.4\n'))
    # todo: anything else that can be checked?... can pdfkit perhaps parse PDFs?...

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
