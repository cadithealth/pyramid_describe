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

def restEnhancer(entry, options):
  if not entry or entry.path != '/rest?_method=POST':
    return entry
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
  'exclude': '^/desc(/.*)?$',
  'format.default': 'rst',
  'format.default.showLegend': 'false',
  'format.default.showGenerator': 'false',
  'format.default.showLocation': 'false',
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
        view=self, root='/', settings={'exclude': '^/desc(/.*)?$'})
    RootController.__init__ = ridiculous_init_override
    # /TODO
    self.app = main({})
    self.testapp = TestApp(self.app)
    res = self.testapp.get('/desc?format=txt')
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
    root.desc = DescribeController(root, doc='URL \t  tree\n    description.')
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
      settings={'exclude': '^/desc(/.*)?$', 'format.default.ascii': 'true'})
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
      settings={'exclude': '^/desc(/.*)?$'})
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
      settings={'exclude': '^/desc(/.*)?$', 'format.default.ascii': 'true', 'filename': 'app'})
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
      settings={'exclude': '^/desc(/.*)?$'})
    self.assertResponse(self.send(root, '/desc/app.txt'), 404)

  #----------------------------------------------------------------------------
  def test_option_redirect(self):
    'The DescribeController can expose a persistent path that redirects to the "real" location'
    root = SimpleRoot()
    root.desc = DescribeController(
      root, doc='URL \t  tree\n    description.',
      settings={'exclude': '^/desc(/.*)?$',
                'formats': 'txt yaml wadl',
                'filename': 'app-v0.3',
                'redirect': 'app'})
    self.assertResponse(self.send(root, '/desc/app.txt'),  302,
                        location='http://localhost/desc/app-v0.3.txt')
    self.assertResponse(self.send(root, '/desc/app.yaml'), 302,
                        location='http://localhost/desc/app-v0.3.yaml')
    self.assertResponse(self.send(root, '/desc/app.wadl'), 302,
                        location='http://localhost/desc/app-v0.3.wadl')
    self.assertResponse(self.send(root, '/desc/app.json'), 404)
    self.assertResponse(self.send(root, '/desc/app.html'), 404)
    self.assertResponse(self.send(root, '/desc/app.xml'),  404)

  #----------------------------------------------------------------------------
  def test_include(self):
    'Setting the Describer `include` parameter is exclusive'
    root = SimpleRoot()
    root.desc = DescribeController(
      root, doc='URL tree description.',
      settings={'include': '^/sub/method$'})
    self.assertResponse(self.send(root, '/desc?format=txt'), 200, '''\
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
      settings={'exclude': ('^/sub/method$', '^/desc(/.*)?$')})
    self.assertResponse(self.send(root, '/desc?format=txt'), 200, '''\
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
      root, doc='URL tree description.', settings={'exclude': '^/desc(/.*)?$'})
    self.assertResponse(self.send(root, '/desc?format=txt'), 200, '''\
/
└── rest/         # RESTful access, with sub-component
    ├── <PUT>     # Modify this object
    ├── access    # Access control
    └── groups    # Return the groups for this object
''')

  #----------------------------------------------------------------------------
  def test_format_rst_full(self):
    'The Describer can render a reStructuredText description'
    root = SimpleRoot()
    root.desc = DescribeController(
      root, doc='URL tree description.',
      settings={'exclude': '^/desc/.*',
                'format.default': 'rst',
                'format.default.showImpl': 'true',
                'filters': restEnhancer})
    self.assertResponse(self.send(root, '/desc'), 200, '''\
Contents of "/"
***************

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

  Supported Methods
  -----------------

  * **DELETE**:

    Handler: pyramid_describe.test.Rest().delete [method]

    Deletes the entry.

  * **GET**:

    Handler: pyramid_describe.test.Rest().get [method]

    Gets the current value.

  * **POST**:

    Handler: pyramid_describe.test.Rest().post [method]

    Creates a new entry.

    :Parameters:

    **size** : int, optional, default 4096

      The anticipated maximum size

    **text** : str

      The text content for the posting

    :Returns:

    **str**

      The ID of the new posting

    :Raises:

    **HTTPUnauthorized**

      Authenticated access is required

    **HTTPForbidden**

      The user does not have posting privileges

  * **PUT**:

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

Legend
******

  * `{{NAME}}`:

    Placeholder -- usually replaced with an ID or other identifier of a RESTful
    object.

  * `<NAME>`:

    Not an actual endpoint, but the HTTP method to use.

  * `NAME/?`:

    Dynamically evaluated endpoint; no further information can be determined
    without request-specific details.

  * `*`:

    This endpoint is a `default` handler, and is therefore free to interpret
    path arguments dynamically; no further information can be determined
    without request-specific details.

  * `...`:

    This endpoint is a `lookup` handler, and is therefore free to interpret
    path arguments dynamically; no further information can be determined
    without request-specific details.

.. generator: pyramid-describe/{version} [format=rst]
.. location: http://localhost/desc
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
Contents of "/"
***************

/rest
=====

  RESTful access, with sub-component

  Supported Methods
  -----------------

  * **PUT**:

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
Contents of "/"
***************

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
      settings={'filters': restEnhancer, 'exclude': '^/desc/.*$'})
    res = self.send(root, '/desc')
    chk = '''\
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" lang="en" xml:lang="en">
 <head>
  <title>Contents of "/"</title>
  <meta http-equiv="content-type" content="text/html; charset=UTF-8"/>
  <meta name="generator" content="pyramid-describe/{version}"/>
  <meta name="pdfkit-page-size" content="A4"/>
  <meta name="pdfkit-orientation" content="Portrait"/>
  <meta name="pdfkit-margin-top" content="10mm"/>
  <meta name="pdfkit-margin-right" content="10mm"/>
  <meta name="pdfkit-margin-bottom" content="10mm"/>
  <meta name="pdfkit-margin-left" content="10mm"/>
  <style type="text/css">
    
     dl{{margin-left: 2em;}}
     dt{{font-weight: bold;}}
     dd{{margin:0.5em 0 0.75em 2em;}}
     .params .param-spec{{font-style: italic;}}
    
   </style>
 </head>
 <body>
  <h1>Contents of "/"</h1>
  <dl class="endpoints">
   <dt id="endpoint-_2F"><h2>/</h2></dt>
   <dd>
    <p>The default root.</p>
   </dd>
   <dt id="endpoint-_2Fdesc"><h2>/desc</h2></dt>
   <dd>
    <p>URL tree description.</p>
   </dd>
   <dt id="endpoint-_2Frest"><h2>/rest</h2></dt>
   <dd>
    <p>A RESTful entry.</p>
    <h3>Supported Methods</h3>
    <dl class="methods">
     <dt id="method-_2Frest-DELETE"><h4>DELETE</h4></dt>
     <dd>
      <p>Deletes the entry.</p>
     </dd>
     <dt id="method-_2Frest-GET"><h4>GET</h4></dt>
     <dd>
      <p>Gets the current value.</p>
     </dd>
     <dt id="method-_2Frest-POST"><h4>POST</h4></dt>
     <dd>
      <p>Creates a new entry.</p>
      <h5>Parameters</h5>
      <dl class="params">
       <dt id="param-_2Frest_3F_5Fmethod_3DPOST-size"><h6>size</h6></dt>
       <dd>
        <div class="param-spec">int, optional, default 4096</div>
        <p>The anticipated maximum size</p>
       </dd>
       <dt id="param-_2Frest_3F_5Fmethod_3DPOST-text"><h6>text</h6></dt>
       <dd>
        <div class="param-spec">str</div>
        <p>The text content for the posting</p>
       </dd>
      </dl>
      <h5>Returns</h5>
      <dl class="returns">
       <dt id="return-_2Frest_3F_5Fmethod_3DPOST-0-str"><h6>str</h6></dt>
       <dd>
        <p>The ID of the new posting</p>
       </dd>
      </dl>
      <h5>Raises</h5>
      <dl class="raises">
       <dt id="raise-_2Frest_3F_5Fmethod_3DPOST-0-HTTPUnauthorized"><h6>HTTPUnauthorized</h6></dt>
       <dd>
        <p>Authenticated access is required</p>
       </dd>
       <dt id="raise-_2Frest_3F_5Fmethod_3DPOST-1-HTTPForbidden"><h6>HTTPForbidden</h6></dt>
       <dd>
        <p>The user does not have posting privileges</p>
       </dd>
      </dl>
     </dd>
     <dt id="method-_2Frest-PUT"><h4>PUT</h4></dt>
     <dd>
      <p>Updates the value.</p>
     </dd>
    </dl>
   </dd>
   <dt id="endpoint-_2Fsub_2Fmethod"><h2>/sub/method</h2></dt>
   <dd>
    <p>This method outputs a JSON list.</p>
   </dd>
   <dt id="endpoint-_2Fswi"><h2>/swi</h2></dt>
   <dd>
    <p>A sub-controller providing only an index.</p>
   </dd>
   <dt id="endpoint-_2Funknown"><h2>/unknown/?</h2></dt>
   <dd>
    <p>A dynamically generated sub-controller.</p>
   </dd>
  </dl>
  <h1 class="legend">Legend</h1>
  <dl class="legend">
   <dt><h2>{{NAME}}</h2></dt>
   <dd>
    <p>Placeholder -- usually replaced with an ID or other identifier of a RESTful object.</p>
   </dd>
   <dt><h2>&lt;NAME&gt;</h2></dt>
   <dd>
    <p>Not an actual endpoint, but the HTTP method to use.</p>
   </dd>
   <dt><h2>NAME/?</h2></dt>
   <dd>
    <p>Dynamically evaluated endpoint; no further information can be determined without request-specific details.</p>
   </dd>
   <dt><h2>*</h2></dt>
   <dd>
    <p>This endpoint is a `default` handler, and is therefore free to interpret path arguments dynamically; no further information can be determined without request-specific details.</p>
   </dd>
   <dt><h2>...</h2></dt>
   <dd>
    <p>This endpoint is a `lookup` handler, and is therefore free to interpret path arguments dynamically; no further information can be determined without request-specific details.</p>
   </dd>
  </dl>
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
       settings={'format.default': 'json', 'filters': restEnhancer, 'exclude': '^/desc/.*'})
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
       settings={'format.default': 'yaml', 'filters': restEnhancer, 'exclude': '^/desc/.*'})
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
       settings={'format.default': 'yaml', 'filters': restEnhancer, 'exclude': '^/desc/.*'})
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
      settings={'format.default': 'xml', 'filters': restEnhancer, 'exclude': '^/desc/.*'})
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
       settings={'format.default': 'wadl', 'filters': restEnhancer, 'exclude': '^/desc/.*'})
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
       settings={'format.default': 'pdf', 'filters': restEnhancer, 'exclude': '^/desc/.*'})
    res = self.send(root, '/desc')
    # todo: check content-type...
    self.assertTrue(res.body.startswith('%PDF-1.4\n'))
    # todo: anything else that can be checked?... can pdfkit perhaps parse PDFs?...

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
