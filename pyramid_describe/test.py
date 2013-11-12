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
from pyramid_describe.rst import AsIs
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
    adict(id='param-2f726573743f5f6d6574686f643d504f5354-73697a65', name='size', type='int',
          default=4096, optional=True, doc='The anticipated maximum size'),
    adict(id='param-2f726573743f5f6d6574686f643d504f5354-74657874', name='text', type='str',
          optional=False, doc='The text content for the posting'),
    )
  entry.returns = (adict(id='return-2f726573743f5f6d6574686f643d504f5354-30-737472', type='str',
                         doc='The ID of the new posting'),)
  entry.raises  = (
    adict(id='raise-2f726573743f5f6d6574686f643d504f5354-30-48545450556e617574686f72697a6564',
          type='HTTPUnauthorized', doc='Authenticated access is required'),
    adict(id='raise-2f726573743f5f6d6574686f643d504f5354-31-48545450466f7262696464656e',
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
def pdfclean(pdf):
  return re.sub('^/CreationDate \(D:[0-9\'-]+\)$', '', pdf, flags=re.MULTILINE)

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
    ## The Describer can render a plain-text hierarchy
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
    ## The Describer can limit plain-text to 7-bit ASCII characters only (via global settings)
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
    ## The Describer can limit plain-text to 7-bit ASCII characters only (via query-string)
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
    ## The DescribeController can use a URL path other than "application.{EXT}"
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
    ## The DescribeController responds with 404 for unknown path requests
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
    ## The DescribeController can expose a persistent path that redirects to the "real" location
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
    ## The DescribeController redirects the index request to the fullname when no basename
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
    ## The DescribeController index redirect option allows 301
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
    ## The DescribeController index redirect option allows explicit URL
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
    ## The DescribeController index redirect option allows explicit URL
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
    ## The DescribeController index redirect option allows explicit URL
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
    ## Setting the Describer `include` parameter is exclusive
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
    ## Setting the Describer `exclude` parameter is inclusive
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
    ## By default, no request options are honored during rendering
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
  def test_request_option_control_enable_all_txt(self):
    ## The rendering options pulled from the request parameters can be set to all options (txt)
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

  #----------------------------------------------------------------------------
  def test_request_option_control_enable_all_rst(self):
    ## The rendering options pulled from the request parameters can be set to all options (rst)
    root = SimpleRoot()
    root.desc = DescribeController(
      root, doc='URL tree description.',
      settings={
        'formats': 'rst',
        'index-redirect': 'false',
        'exclude': ('|^/sub/method$|', '|^/desc(/.*)?$|'),
        'format.request': 'true',
        })
    self.assertResponse(self.send(root, '/desc?showRest=false&showInfo=false&showLegend=false&showMeta=false&rstMax=true'), 200, '''\
.. title:: Contents of "/"

.. class:: endpoints

.. _`section-endpoints`:

===============
Contents of "/"
===============

* \/

* /rest

* /swi

* /unknown/?
''')

  #----------------------------------------------------------------------------
  def test_request_option_control_enable_all_html(self):
    ## The rendering options pulled from the request parameters can be set to all options (html)
    root = SimpleRoot()
    root.desc = DescribeController(
      root, doc='URL tree description.',
      settings={
        'formats': 'txt',
        'index-redirect': 'false',
        'exclude': ('|^/sub/method$|', '|^/desc(/.*)?$|'),
        'format.request': 'true',
        })
    chk = '''\
<?xml version="1.0" encoding="UTF-8" ?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
 <head>
  <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
  <meta name="generator" content="Docutils 0.10: http://docutils.sourceforge.net/" />
  <title>Contents of &quot;/&quot;</title>
 </head>
 <body>
  <div class="document">
   <div class="endpoints section" id="section-endpoints">
    <h1 class="section-title">Contents of &quot;/&quot;</h1>
    <ul class="simple">
     <li>/</li>
     <li>/rest</li>
     <li>/swi</li>
     <li>/unknown/?</li>
    </ul>
   </div>
  </div>
 </body>
</html>
'''
    chk = re.sub('>\s*<', '><', chk, flags=re.MULTILINE)
    res = self.send(root, '/desc?format=html&showRest=false&showInfo=false&showLegend=false&cssPath=&showMeta=false')
    res.body = re.sub('>\s*<', '><', res.body, flags=re.MULTILINE)
    self.assertResponse(res, 200, chk, xml=True)

  #----------------------------------------------------------------------------
  def test_request_option_control_enable_list(self):
    ## The rendering options pulled from the request parameters can be a list of specific options
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
    ## The Describer supports mixing RESTful and URL component methods in "txt" format
    class Access(Controller):
      @index(forceSlash=False)
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
  def test_format_txt_differentiates_forced_slash_index(self):
    ## The Describer can differentiate a forced-slash index
    class SubIndexForceSlash(Controller):
      @index(forceSlash=True)
      def myindex(self, request):
        'A sub-controller providing only a slash-index.'
        return 'my.index'
    root = SimpleRoot()
    root.swfs = SubIndexForceSlash()
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
├── swfs/
├── swi
└── unknown/?
''')

  #----------------------------------------------------------------------------
  def test_format_rst_standard(self):
    ## The Describer can render a reStructuredText description
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

------
\/
------

Handler: pyramid_describe.test.SimpleRoot() [instance]

The default root.

------
/desc
------

Handler: pyramid_describe.controller.DescribeController() [instance]

URL tree description.

------
/rest
------

Handler: pyramid_describe.test.Rest() [instance]

A RESTful entry.

```````
Methods
```````

::::::
DELETE
::::::

Handler: pyramid_describe.test.Rest().delete [method]

Deletes the entry.

::::::
GET
::::::

Handler: pyramid_describe.test.Rest().get [method]

Gets the current value.

::::::
POST
::::::

Handler: pyramid_describe.test.Rest().post [method]

Creates a new entry.

''\'''\'''\''
Parameters
''\'''\'''\''

""""""
size
""""""

int, optional, default 4096

The anticipated maximum size

""""""
text
""""""

str

The text content for the posting

''\'''\''
Returns
''\'''\''

""""""
str
""""""

The ID of the new posting

''\'''\'
Raises
''\'''\'

""""""""""""""""
HTTPUnauthorized
""""""""""""""""

Authenticated access is required

"""""""""""""
HTTPForbidden
"""""""""""""

The user does not have posting privileges

::::::
PUT
::::::

Handler: pyramid_describe.test.Rest().put [method]

Updates the value.

-----------
/sub/method
-----------

Handler: pyramid_describe.test.Sub().method [method]

This method outputs a JSON list.

------
/swi
------

Handler: pyramid_describe.test.SubIndex() [instance]

A sub-controller providing only an index.

----------
/unknown/?
----------

Handler: pyramid_describe.test.Unknown [class]

A dynamically generated sub-controller.

======
Legend
======

------
{{NAME}}
------

Placeholder -- usually replaced with an ID or other identifier of a RESTful
object.

------
<NAME>
------

Not an actual endpoint, but the HTTP method to use.

------
NAME/?
------

Dynamically evaluated endpoint; no further information can be determined
without request-specific details.

------
\*
------

This endpoint is a `default` handler, and is therefore free to interpret path
arguments dynamically; no further information can be determined without
request-specific details.

------
\.\.\.
------

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
    ## The Describer can change the reStructuredText title based on options
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

------
/swi
------

Handler: pyramid_describe.test.SubIndex() [instance]

A sub-controller providing only an index.

======
Legend
======

------
{{NAME}}
------

Placeholder -- usually replaced with an ID or other identifier of a RESTful
object.

------
<NAME>
------

Not an actual endpoint, but the HTTP method to use.

------
NAME/?
------

Dynamically evaluated endpoint; no further information can be determined
without request-specific details.

------
\*
------

This endpoint is a `default` handler, and is therefore free to interpret path
arguments dynamically; no further information can be determined without
request-specific details.

------
\.\.\.
------

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
    ## The Describer renders reStructuredText with maximum decorations
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

.. _`section-endpoints`:

===============
Contents of "/"
===============

.. class:: endpoint

.. _`endpoint-2f`:

------
\/
------

.. class:: handler

.. _`handler-endpoint-2f`:

Handler: pyramid_describe.test.SimpleRoot() [instance]

The default root.

.. class:: endpoint

.. _`endpoint-2f64657363`:

------
/desc
------

.. class:: handler

.. _`handler-endpoint-2f64657363`:

Handler: pyramid_describe.controller.DescribeController() [instance]

URL tree description.

.. class:: endpoint

.. _`endpoint-2f72657374`:

------
/rest
------

.. class:: handler

.. _`handler-endpoint-2f72657374`:

Handler: pyramid_describe.test.Rest() [instance]

A RESTful entry.

.. class:: methods

.. _`methods-endpoint-2f72657374`:

```````
Methods
```````

.. class:: method

.. _`method-2f72657374-44454c455445`:

::::::
DELETE
::::::

.. class:: handler

.. _`handler-method-2f72657374-44454c455445`:

Handler: pyramid_describe.test.Rest().delete [method]

Deletes the entry.

.. class:: method

.. _`method-2f72657374-474554`:

::::::
GET
::::::

.. class:: handler

.. _`handler-method-2f72657374-474554`:

Handler: pyramid_describe.test.Rest().get [method]

Gets the current value.

.. class:: fake-docs-here method post-is-not-put

.. _`method-2f72657374-504f5354`:

::::::
POST
::::::

.. class:: handler

.. _`handler-method-2f72657374-504f5354`:

Handler: pyramid_describe.test.Rest().post [method]

Creates a new entry.

.. class:: params

.. _`params-method-2f72657374-504f5354`:

''\'''\'''\''
Parameters
''\'''\'''\''

.. class:: param

.. _`param-method-2f72657374-504f5354-73697a65`:

""""""
size
""""""

.. class:: spec

int, optional, default 4096

The anticipated maximum size

.. class:: param

.. _`param-method-2f72657374-504f5354-74657874`:

""""""
text
""""""

.. class:: spec

str

The text content for the posting

.. class:: returns

.. _`returns-method-2f72657374-504f5354`:

''\'''\''
Returns
''\'''\''

.. class:: return

.. _`return-method-2f72657374-504f5354-737472`:

""""""
str
""""""

The ID of the new posting

.. class:: raises

.. _`raises-method-2f72657374-504f5354`:

''\'''\'
Raises
''\'''\'

.. class:: raise

.. _`raise-method-2f72657374-504f5354-48545450556e617574686f72697a6564`:

""""""""""""""""
HTTPUnauthorized
""""""""""""""""

Authenticated access is required

.. class:: raise

.. _`raise-method-2f72657374-504f5354-48545450466f7262696464656e`:

"""""""""""""
HTTPForbidden
"""""""""""""

The user does not have posting privileges

.. class:: method

.. _`method-2f72657374-505554`:

::::::
PUT
::::::

.. class:: handler

.. _`handler-method-2f72657374-505554`:

Handler: pyramid_describe.test.Rest().put [method]

Updates the value.

.. class:: endpoint

.. _`endpoint-2f7375622f6d6574686f64`:

-----------
/sub/method
-----------

.. class:: handler

.. _`handler-endpoint-2f7375622f6d6574686f64`:

Handler: pyramid_describe.test.Sub().method [method]

This method outputs a JSON list.

.. class:: endpoint sub-with-index

.. _`endpoint-2f737769`:

------
/swi
------

.. class:: handler

.. _`handler-endpoint-2f737769`:

Handler: pyramid_describe.test.SubIndex() [instance]

A sub-controller providing only an index.

.. class:: endpoint

.. _`endpoint-2f756e6b6e6f776e`:

----------
/unknown/?
----------

.. class:: handler

.. _`handler-endpoint-2f756e6b6e6f776e`:

Handler: pyramid_describe.test.Unknown [class]

A dynamically generated sub-controller.

.. class:: legend

.. _`section-legend`:

======
Legend
======

.. class:: legend-item

.. _`legend-item-7b4e414d457d`:

------
{{NAME}}
------

Placeholder -- usually replaced with an ID or other identifier of a RESTful
object.

.. class:: legend-item

.. _`legend-item-3c4e414d453e`:

------
<NAME>
------

Not an actual endpoint, but the HTTP method to use.

.. class:: legend-item

.. _`legend-item-4e414d452f3f`:

------
NAME/?
------

Dynamically evaluated endpoint; no further information can be determined
without request-specific details.

.. class:: legend-item

.. _`legend-item-2a`:

------
\*
------

This endpoint is a `default` handler, and is therefore free to interpret path
arguments dynamically; no further information can be determined without
request-specific details.

.. class:: legend-item

.. _`legend-item-2e2e2e`:

------
\.\.\.
------

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
    ## The Describer supports mixing RESTful and URL component methods in "rst" format
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

------
/rest
------

RESTful access, with sub-component

```````
Methods
```````

::::::
PUT
::::::

Modify this object

------------
/rest/access
------------

Access control

------------
/rest/groups
------------

Return the groups for this object
''')

  #----------------------------------------------------------------------------
  def test_prune_index(self):
    ## The Describer can collapse up index docs
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

------
\/
------

The index method
''')

  #----------------------------------------------------------------------------
  def test_restructuredtext_in_documentation(self):
    ## The Describer can integrate reStructuredText from docstrings
    class Root(Controller):
      @index
      def index(self, request):
        '''
        Current list of **states** that this
        controller
        can be in (long line to cause line wrapping):

        * beta
        * production
        * deprecated

        The following `skill` levels exist:

        ``Novice``:
          a true beginner.
        ``Intermediate``:
          an average user.
        ``Expert``:
          the sky is the limit.
        '''
    root = Root()
    root.desc = DescribeController(
      root, doc='URL tree description.',
       settings=settings_minRst)
    self.assertResponse(self.send(root, '/desc'), 200, '''\
===============
Contents of "/"
===============

------
\/
------

Current list of **states** that this controller can be in (long line to cause
line wrapping):

* beta

* production

* deprecated

The following `skill` levels exist:

``Novice``:

    a true beginner.

``Intermediate``:

    an average user.

``Expert``:

    the sky is the limit.
''')

  #----------------------------------------------------------------------------
  def test_format_html(self):
    ## The Describer can render HTML
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

.section {{
  padding-left: 30px;
}}

.section > .section-title {{
  margin-left: -30px;
}}

.document > .section > .section-title {{
  margin-top: 0;
}}

.document > .section {{
  padding-left: 0;
}}

.document > .section > .section-title {{
  margin-left: 0;
}}

#section-legend {{
  font-size: 70%;
  margin-top: 5em;
  border-top: 2px solid #e0e0e0;
  padding-top: 1em;
}}

</style>
 </head>
 <body>
  <div class="document">
   <div class="endpoints section" id="section-endpoints">
    <h1 class="section-title">Application API</h1>
    <div class="endpoint section" id="endpoint-2f">
     <h2 class="section-title">/</h2>
     <p>The default root.</p>
    </div>
    <div class="endpoint section" id="endpoint-2f64657363">
     <h2 class="section-title">/desc</h2>
     <p>URL tree description.</p>
    </div>
    <div class="endpoint section" id="endpoint-2f72657374">
     <h2 class="section-title">/rest</h2>
     <p>A RESTful entry.</p>
     <div class="methods section" id="methods-endpoint-2f72657374">
      <h3 class="section-title">Methods</h3>
      <div class="method section" id="method-2f72657374-44454c455445">
       <h4 class="section-title">DELETE</h4>
       <p>Deletes the entry.</p>
      </div>
      <div class="method section" id="method-2f72657374-474554">
       <h4 class="section-title">GET</h4>
       <p>Gets the current value.</p>
      </div>
      <div class="fake-docs-here method post-is-not-put section" id="method-2f72657374-504f5354">
       <h4 class="section-title">POST</h4>
       <p>Creates a new entry.</p>
       <div class="params section" id="params-method-2f72657374-504f5354">
        <h5 class="section-title">Parameters</h5>
        <div class="param section" id="param-method-2f72657374-504f5354-73697a65">
         <h6 class="section-title">size</h6>
         <p class="spec">int, optional, default 4096</p>
         <p>The anticipated maximum size</p>
        </div>
        <div class="param section" id="param-method-2f72657374-504f5354-74657874">
         <h6 class="section-title">text</h6>
         <p class="spec">str</p>
         <p>The text content for the posting</p>
        </div>
       </div>
       <div class="returns section" id="returns-method-2f72657374-504f5354">
        <h5 class="section-title">Returns</h5>
        <div class="return section" id="return-method-2f72657374-504f5354-737472">
         <h6 class="section-title">str</h6>
         <p>The ID of the new posting</p>
        </div>
       </div>
       <div class="raises section" id="raises-method-2f72657374-504f5354">
        <h5 class="section-title">Raises</h5>
        <div class="raise section" id="raise-method-2f72657374-504f5354-48545450556e617574686f72697a6564">
         <h6 class="section-title">HTTPUnauthorized</h6>
         <p>Authenticated access is required</p>
        </div>
        <div class="raise section" id="raise-method-2f72657374-504f5354-48545450466f7262696464656e">
         <h6 class="section-title">HTTPForbidden</h6>
         <p>The user does not have posting privileges</p>
        </div>
       </div>
      </div>
      <div class="method section" id="method-2f72657374-505554">
       <h4 class="section-title">PUT</h4>
       <p>Updates the value.</p>
      </div>
     </div>
    </div>
    <div class="endpoint section" id="endpoint-2f7375622f6d6574686f64">
     <h2 class="section-title">/sub/method</h2>
     <p>This method outputs a JSON list.</p>
    </div>
    <div class="endpoint section sub-with-index" id="endpoint-2f737769">
     <h2 class="section-title">/swi</h2>
     <p>A sub-controller providing only an index.</p>
    </div>
    <div class="endpoint section" id="endpoint-2f756e6b6e6f776e">
     <h2 class="section-title">/unknown/?</h2>
     <p>A dynamically generated sub-controller.</p>
    </div>
   </div>
   <div class="legend section" id="section-legend">
    <h1 class="section-title">Legend</h1>
    <div class="legend-item section" id="legend-item-7b4e414d457d">
     <h2 class="section-title">{{NAME}}</h2>
     <p>Placeholder -- usually replaced with an ID or other identifier of a RESTful
object.</p>
    </div>
    <div class="legend-item section" id="legend-item-3c4e414d453e">
     <h2 class="section-title">&lt;NAME&gt;</h2>
     <p>Not an actual endpoint, but the HTTP method to use.</p>
    </div>
    <div class="legend-item section" id="legend-item-4e414d452f3f">
     <h2 class="section-title">NAME/?</h2>
     <p>Dynamically evaluated endpoint; no further information can be determined
without request-specific details.</p>
    </div>
    <div class="legend-item section" id="legend-item-2a">
     <h2 class="section-title">*</h2>
     <p>This endpoint is a <cite>default</cite> handler, and is therefore free to interpret path
arguments dynamically; no further information can be determined without
request-specific details.</p>
    </div>
    <div class="legend-item section" id="legend-item-2e2e2e">
     <h2 class="section-title">...</h2>
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
  def test_AsIs(self):
    ## The Describer honors the format-specific `filters` option
    from docutils import nodes
    def fiddler(doc, options):
      doc['classes'].append('fiddled')
      def specials(node):
        return [n for n in node.children if isinstance(n, nodes.Special)] \
          + [sn for n in node.children for sn in specials(n)]
      keep = specials(doc)
      doc.children = []
      doc.extend(keep)
      doc.append(nodes.paragraph('', '', nodes.Text('some text.')))
      doc.append(AsIs('''\
<script>
  alert('hello, world!');
</script>
'''))
      return doc
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
        'format.html.default.filters': fiddler,
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
  <div class="document fiddled">
   <p>some text.</p>
<script>
  alert('hello, world!');
</script>
  </div>
 </body>
</html>
'''.format(version=getVersion('pyramid_describe'))

    chk = re.sub('>\s*<', '><', chk, flags=re.MULTILINE)
    res.body = re.sub('>\s*<', '><', res.body, flags=re.MULTILINE)
    self.assertResponse(res, 200, chk, xml=True)

  #----------------------------------------------------------------------------
  def test_format_json(self):
    ## The Describer can render JSON
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
        "id": "endpoint-2f",
        "path": "/",
        "decoratedName": "",
        "decoratedPath": "/",
        "doc": "The default root."
      },
      { "name": "desc",
        "id": "endpoint-2f64657363",
        "path": "/desc",
        "decoratedName": "desc",
        "decoratedPath": "/desc",
        "doc": "URL tree description."
      },
      { "name": "rest",
        "id": "endpoint-2f72657374",
        "path": "/rest",
        "decoratedName": "rest",
        "decoratedPath": "/rest",
        "doc": "A RESTful entry.",
        "methods": [
          { "name": "DELETE",
            "id": "method-2f72657374-44454c455445",
            "doc": "Deletes the entry."
          },
          { "name": "GET",
            "id": "method-2f72657374-474554",
            "doc": "Gets the current value."
          },
          { "name": "POST",
            "id": "method-2f72657374-504f5354",
            "doc": "Creates a new entry.",
            "params": [
              { "name": "size",
                "id": "param-2f726573743f5f6d6574686f643d504f5354-73697a65",
                "type": "int",
                "optional": true,
                "default": 4096,
                "doc": "The anticipated maximum size"
              },
              { "name": "text",
                "id": "param-2f726573743f5f6d6574686f643d504f5354-74657874",
                "type": "str",
                "optional": false,
                "doc": "The text content for the posting"
              }
            ],
            "returns": [
              { "type": "str",
                "id": "return-2f726573743f5f6d6574686f643d504f5354-30-737472",
                "doc": "The ID of the new posting"
              }
            ],
            "raises": [
              { "type": "HTTPUnauthorized",
                "id": "raise-2f726573743f5f6d6574686f643d504f5354-30-48545450556e617574686f72697a6564",
                "doc": "Authenticated access is required"
              },
              { "type": "HTTPForbidden",
                "id": "raise-2f726573743f5f6d6574686f643d504f5354-31-48545450466f7262696464656e",
                "doc": "The user does not have posting privileges"
              }
            ]
          },
          { "name": "PUT",
            "id": "method-2f72657374-505554",
            "doc": "Updates the value."
          }
        ]
      },
      { "name": "method",
        "id": "endpoint-2f7375622f6d6574686f64",
        "path": "/sub/method",
        "decoratedName": "method",
        "decoratedPath": "/sub/method",
        "doc": "This method outputs a JSON list."
      },
      { "name": "swi",
        "id": "endpoint-2f737769",
        "path": "/swi",
        "decoratedName": "swi",
        "decoratedPath": "/swi",
        "doc": "A sub-controller providing only an index."
      },
      { "name": "unknown",
        "id": "endpoint-2f756e6b6e6f776e",
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
    ## The Describer can render YAML
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
      id: 'endpoint-2f'
      path: /
      decoratedName: ''
      decoratedPath: /
      doc: The default root.
    - name: desc
      id: 'endpoint-2f64657363'
      path: /desc
      decoratedName: desc
      decoratedPath: /desc
      doc: URL tree description.
    - name: rest
      id: 'endpoint-2f72657374'
      path: /rest
      decoratedName: rest
      decoratedPath: /rest
      doc: A RESTful entry.
      methods:
        - name: DELETE
          id: 'method-2f72657374-44454c455445'
          doc: Deletes the entry.
        - name: GET
          id: 'method-2f72657374-474554'
          doc: Gets the current value.
        - name: POST
          id: 'method-2f72657374-504f5354'
          doc: Creates a new entry.
          params:
            - name: size
              id: 'param-2f726573743f5f6d6574686f643d504f5354-73697a65'
              type: int
              optional: true
              default: 4096
              doc: The anticipated maximum size
            - name: text
              id: 'param-2f726573743f5f6d6574686f643d504f5354-74657874'
              type: str
              optional: false
              doc: The text content for the posting
          returns:
            - type: str
              id: 'return-2f726573743f5f6d6574686f643d504f5354-30-737472'
              doc: The ID of the new posting
          raises:
            - type: HTTPUnauthorized
              id: 'raise-2f726573743f5f6d6574686f643d504f5354-30-48545450556e617574686f72697a6564'
              doc: Authenticated access is required
            - type: HTTPForbidden
              id: 'raise-2f726573743f5f6d6574686f643d504f5354-31-48545450466f7262696464656e'
              doc: The user does not have posting privileges
        - name: PUT
          id: 'method-2f72657374-505554'
          doc: Updates the value.
    - name: method
      id: 'endpoint-2f7375622f6d6574686f64'
      path: /sub/method
      decoratedName: method
      decoratedPath: /sub/method
      doc: This method outputs a JSON list.
    - name: swi
      id: 'endpoint-2f737769'
      path: /swi
      decoratedName: swi
      decoratedPath: /swi
      doc: A sub-controller providing only an index.
    - name: unknown
      id: 'endpoint-2f756e6b6e6f776e'
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
    ## The Describer renders YAML with dedented documentation
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
      id: 'endpoint-2f64657363'
      path: /desc
      decoratedName: desc
      decoratedPath: /desc
      doc: URL tree description.
    - name: describe
      id: 'endpoint-2f6465736372696265'
      path: /describe
      decoratedName: describe
      decoratedPath: /describe
      doc: "A multi-line\\ncomment."
'''
    self.assertEqual(yaml.load(res.body), yaml.load(chk))

  #----------------------------------------------------------------------------
  def test_format_xml(self):
    ## The Describer can render XML
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
 <endpoint name="" path="/" decorated-name="" decorated-path="/" id="endpoint-2f">
  <doc>The default root.</doc>
 </endpoint>
 <endpoint name="desc" path="/desc" decorated-name="desc" decorated-path="/desc" id="endpoint-2f64657363">
  <doc>URL tree description.</doc>
 </endpoint>
 <endpoint name="rest" path="/rest" decorated-name="rest" decorated-path="/rest" id="endpoint-2f72657374">
  <doc>A RESTful entry.</doc>
  <method id="method-2f72657374-44454c455445" name="DELETE"><doc>Deletes the entry.</doc></method>
  <method id="method-2f72657374-474554" name="GET"><doc>Gets the current value.</doc></method>
  <method id="method-2f72657374-504f5354" name="POST">
   <doc>Creates a new entry.</doc>
   <param default="4096" id="param-2f726573743f5f6d6574686f643d504f5354-73697a65" name="size" optional="True" type="int">
    <doc>The anticipated maximum size</doc>
   </param>
   <param id="param-2f726573743f5f6d6574686f643d504f5354-74657874" name="text" optional="False" type="str">
    <doc>The text content for the posting</doc>
   </param>
   <return id="return-2f726573743f5f6d6574686f643d504f5354-30-737472" type="str">
    <doc>The ID of the new posting</doc>
   </return>
   <raise id="raise-2f726573743f5f6d6574686f643d504f5354-30-48545450556e617574686f72697a6564" type="HTTPUnauthorized">
    <doc>Authenticated access is required</doc>
   </raise>
   <raise id="raise-2f726573743f5f6d6574686f643d504f5354-31-48545450466f7262696464656e" type="HTTPForbidden">
    <doc>The user does not have posting privileges</doc>
   </raise>
  </method>
  <method id="method-2f72657374-505554" name="PUT"><doc>Updates the value.</doc></method>
 </endpoint>
 <endpoint name="method" path="/sub/method" decorated-name="method" decorated-path="/sub/method" id="endpoint-2f7375622f6d6574686f64">
  <doc>This method outputs a JSON list.</doc>
 </endpoint>
 <endpoint name="swi" path="/swi" decorated-name="swi" decorated-path="/swi" id="endpoint-2f737769">
  <doc>A sub-controller providing only an index.</doc>
 </endpoint>
 <endpoint name="unknown" path="/unknown" decorated-name="unknown/?" decorated-path="/unknown/?" id="endpoint-2f756e6b6e6f776e">
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
    ## The Describer can render WADL
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
  <resource id="endpoint-2f" path="">
   <pd:doc>The default root.</pd:doc>
   <method id="method-2f-474554" name="GET"/>
  </resource>
  <resource id="endpoint-2f64657363" path="desc">
   <pd:doc>URL tree description.</pd:doc>
   <method id="method-2f64657363-474554" name="GET"/>
  </resource>
  <resource id="endpoint-2f72657374" path="rest">
   <pd:doc>A RESTful entry.</pd:doc>
   <method id="method-2f72657374-44454c455445" name="DELETE">
    <pd:doc>Deletes the entry.</pd:doc>
   </method>
   <method id="method-2f72657374-474554" name="GET">
    <pd:doc>Gets the current value.</pd:doc>
   </method>
   <method id="method-2f72657374-504f5354" name="POST">
    <pd:doc>Creates a new entry.</pd:doc>
    <request>
     <param id="param-2f726573743f5f6d6574686f643d504f5354-73697a65" name="size" type="xsd:integer" required="false" default="4096">
      <pd:doc>The anticipated maximum size</pd:doc>
     </param>
     <param id="param-2f726573743f5f6d6574686f643d504f5354-74657874" name="text" type="xsd:string" required="true">
      <pd:doc>The text content for the posting</pd:doc>
     </param>
    </request>
    <response>
     <representation id="return-2f726573743f5f6d6574686f643d504f5354-30-737472" element="xsd:string">
      <pd:doc>The ID of the new posting</pd:doc>
     </representation>
     <fault id="raise-2f726573743f5f6d6574686f643d504f5354-30-48545450556e617574686f72697a6564" element="HTTPUnauthorized">
      <pd:doc>Authenticated access is required</pd:doc>
     </fault>
     <fault id="raise-2f726573743f5f6d6574686f643d504f5354-31-48545450466f7262696464656e" element="HTTPForbidden">
      <pd:doc>The user does not have posting privileges</pd:doc>
     </fault>
    </response>
   </method>
   <method id="method-2f72657374-505554" name="PUT">
    <pd:doc>Updates the value.</pd:doc>
   </method>
  </resource>
  <resource id="endpoint-2f7375622f6d6574686f64" path="sub/method">
   <pd:doc>This method outputs a JSON list.</pd:doc>
   <method id="method-2f7375622f6d6574686f64-474554" name="GET"/>
  </resource>
  <resource id="endpoint-2f737769" path="swi">
   <pd:doc>A sub-controller providing only an index.</pd:doc>
   <method id="method-2f737769-474554" name="GET"/>
  </resource>
  <resource id="endpoint-2f756e6b6e6f776e" path="unknown">
   <pd:doc>A dynamically generated sub-controller.</pd:doc>
   <method id="method-2f756e6b6e6f776e-474554" name="GET"/>
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
    ## The Describer can render PDF
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

  #----------------------------------------------------------------------------
  def test_renderer_override(self):
    ## Format-specific rendering options can be overriden and cascaded through format chains
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
    pdf_orig = pdfclean(self.send(root, '/desc').body)
    # confirm that pdf renderings stay consistent
    root = SimpleRoot()
    root.desc = DescribeController(
       root, doc='URL tree description.',
       settings={
         'format.default': 'pdf',
         'index-redirect': 'false',
         'entries.filters': docsEnhancer,
         'exclude': '|^/desc/.*|',
         })
    self.assertEqual(pdfclean(self.send(root, '/desc').body), pdf_orig)
    # confirm that fiddling with html css rendering changes pdf
    root = SimpleRoot()
    root.desc = DescribeController(
       root, doc='URL tree description.',
       settings={
         'format.default': 'pdf',
         'index-redirect': 'false',
         'entries.filters': docsEnhancer,
         'exclude': '|^/desc/.*|',
         'format.html.default.cssPath': None,
         })
    self.assertNotEqual(pdfclean(self.send(root, '/desc').body), pdf_orig)
    # confirm that fiddling with html css cascading can be controlled
    root = SimpleRoot()
    root.desc = DescribeController(
       root, doc='URL tree description.',
       settings={
         'format.default': 'pdf',
         'index-redirect': 'false',
         'entries.filters': docsEnhancer,
         'exclude': '|^/desc/.*|',
         'format.html.default.cssPath': None,
         'format.html+pdf.default.cssPath': 'pyramid_describe:DEFAULT',
         })
    self.assertEqual(pdfclean(self.send(root, '/desc').body), pdf_orig)

  #----------------------------------------------------------------------------
  def test_format_rst_and_html_filters(self):
    ## It is possible to filter both the RST and the HTML separately
    from docutils import nodes
    def rst_fiddler(doc, stage):
      doc.children = []
      sect = nodes.section('', nodes.title('', '', nodes.Text('the title')))
      sect.append(nodes.paragraph('', '', nodes.Text('some rst text.')))
      sect['classes'].append('rst-fiddled')
      doc.append(sect)
      return doc
    def html_fiddler(doc, options):
      for node in doc:
        if isinstance(node, nodes.section):
          node['classes'].append('html-fiddled')
          node.append(nodes.paragraph('', '', nodes.Text('some html text.')))
      return doc
    root = SimpleRoot()
    root.desc = DescribeController(
      root, doc='URL tree description.',
      settings={
        'entries.filters': docsEnhancer,
        'index-redirect': 'false',
        'exclude': '|^/desc/.*$|',
        'format.default.showLegend': 'false',
        'format.default.rstPdfkit': 'false',
        'format.rst.default.filters': rst_fiddler,
        'format.html.default.cssPath': None,
        'format.html.default.filters': html_fiddler,
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
 </head>
 <body>
  <div class="document">
   <div class="html-fiddled rst-fiddled section" id="the-title">
    <h1 class="section-title">the title</h1>
    <p>some rst text.</p>
    <p>some html text.</p>
   </div>
  </div>
 </body>
</html>
'''.format(version=getVersion('pyramid_describe'))

    chk = re.sub('>\s*<', '><', chk, flags=re.MULTILINE)
    res.body = re.sub('>\s*<', '><', res.body, flags=re.MULTILINE)
    self.assertResponse(res, 200, chk, xml=True)

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
