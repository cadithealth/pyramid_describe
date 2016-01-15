# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2016/01/12
# copy: (C) Copyright 2016-EOT Cadit Inc., All Rights Reserved.
#------------------------------------------------------------------------------

# import unittest
# import json
import textwrap

# import six
# from aadict import aadict
from pyramid_controllers.test_helpers import TestHelper

#------------------------------------------------------------------------------
class TestAccess(TestHelper):

  #----------------------------------------------------------------------------
  def assertRstEqual(self, a, b, msg=None):
    if a:
      a = textwrap.dedent(a).strip() + '\n'
    if b:
      b = textwrap.dedent(b).strip() + '\n'
    return self.assertMultiLineEqual(a, b, msg=msg)

  #----------------------------------------------------------------------------
  def test_filtering(self):
    from pyramid_controllers import Controller, expose
    from .controller import DescribeController
    from .describer import Describer
    from .typereg import Type, TypeRef
    class Controller(Controller):
      @expose
      def shape(self, request):
        '''
        Returns
        -------
        Shape
          A shape.

          @INTERNAL: the `author` field is internal.
          sides : int
          source : Source
          author : Author, read-only
            The author.
          created : num, @INTERNAL
        '''
      @expose
      def source(self, request):
        '''
        Returns
        -------
        Source
          A source.
          url : str
          created : num, @INTERNAL
        '''
      @expose
      def hidden(self, request):
        '''
        @INTERNAL: This is a hidden API.
        '''

    extensions = textwrap.dedent('''\
      Author
        @INTERNAL

        The author of a shape.

        name : str
    ''')

    def acl(request, *args, **kw):
      return request.params.get('test-access', '').split(',')

    root = Controller()
    root.desc = DescribeController(
      root,
      settings={
        'format.request': 'true',
        'format.default': 'rst',
        'index-redirect': 'false',
        'exclude': '|^/desc(/.*)?$|',
        'access.control': acl,
        'access.default.endpoint': 'public',
        'access.default.type': 'public',
      })
    desc = Describer()
    root.desc.describer.typereg.loadExtensionString(extensions, '<test>')
    desc.typereg.loadExtensionString(extensions, '<test>')

    catalog = desc.analyze(root)

    # self.assertEqual(
    #   catalog.typereg.types(),
    #   [
    #     Type(
    #       base  = 'dict',
    #       name  = 'Author',
    #       doc   = '@INTERNAL\n\nThe author of a shape.',
    #       value = [
    #         TypeRef(name='name', type=Type(base='scalar', name='string')),
    #       ]),
    #     Type(
    #       base  = 'dict',
    #       name  = 'Shape',
    #       doc   = 'A shape.\n\n.. class:: doc-internal\n\n@INTERNAL: the `author` field is internal.',
    #       value = [
    #         TypeRef(name='sides', type=Type(base='scalar', name='integer')),
    #         TypeRef(name='source', type=desc.typereg.get('Source')),
    #         TypeRef(name='author', type=desc.typereg.get('Author'),
    #                 doc='The author.',
    #                 params={'read': True, 'create': False, 'write': False}),
    #         TypeRef(name='created', type=Type(base='scalar', name='number'),
    #                 params={'@INTERNAL': True, 'classes': ['doc-internal']}),
    #       ]),
    #     Type(
    #       base  = 'dict',
    #       name  = 'Source',
    #       doc   = 'A source.',
    #       value = [
    #         # todo: dict parameters are not sorted unless they get merged...
    #         #       they should always be sorted.
    #         TypeRef(name='url', type=Type(base='scalar', name='string')),
    #         TypeRef(name='created', type=Type(base='scalar', name='number'),
    #                 params={'@INTERNAL': True, 'classes': ['doc-internal']}),
    #       ]),
    #   ]
    # )

    # self.assertRstEqual(
    #   self.send(root, '/desc?test-access=public,beta,internal&showLegend=false&showMeta=false').body,
    #   '''
    #     ===============
    #     Contents of "/"
    #     ===============

    #     ---------
    #     Endpoints
    #     ---------

    #     ```````
    #     /hidden
    #     ```````

    #     @INTERNAL: This is a hidden API.

    #     ``````
    #     /shape
    #     ``````

    #     :::::::
    #     Returns
    #     :::::::

    #     ''\'''\'
    #     Shape
    #     ''\'''\'

    #     ```````
    #     /source
    #     ```````

    #     :::::::
    #     Returns
    #     :::::::

    #     ''\'''\'
    #     Source
    #     ''\'''\'

    #     ------
    #     Types
    #     ------

    #     ``````
    #     Author
    #     ``````

    #     @INTERNAL

    #     The author of a shape.

    #     ::::::
    #     name
    #     ::::::

    #     string

    #     ``````
    #     Shape
    #     ``````

    #     A shape.

    #     .. class:: doc-internal

    #     @INTERNAL: the `author` field is internal.

    #     ::::::
    #     sides
    #     ::::::

    #     integer

    #     ::::::
    #     source
    #     ::::::

    #     Source

    #     ::::::
    #     author
    #     ::::::

    #     Author

    #     The author.

    #     :::::::
    #     created
    #     :::::::

    #     number, @INTERNAL

    #     ``````
    #     Source
    #     ``````

    #     A source.

    #     ::::::
    #     url
    #     ::::::

    #     string

    #     :::::::
    #     created
    #     :::::::

    #     number, @INTERNAL
    #   '''
    # )

    self.assertRstEqual(
      self.send(root, '/desc?test-access=public&showLegend=false&showMeta=false').body,
      '''
        ===============
        Contents of "/"
        ===============

        ---------
        Endpoints
        ---------

        ``````
        /shape
        ``````

        :::::::
        Returns
        :::::::

        ''\'''\'
        Shape
        ''\'''\'

        ```````
        /source
        ```````

        :::::::
        Returns
        :::::::

        ''\'''\'
        Source
        ''\'''\'

        ------
        Types
        ------

        ``````
        Shape
        ``````

        A shape.

        .. class:: doc-internal

        @INTERNAL: the `author` field is internal.

        ::::::
        sides
        ::::::

        integer

        ::::::
        source
        ::::::

        Source

        ``````
        Source
        ``````

        A source.

        ::::::
        url
        ::::::

        string
      '''
    )


#------------------------------------------------------------------------------
# end of $Id$
# $ChangeLog$
#------------------------------------------------------------------------------
