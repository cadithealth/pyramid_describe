# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2014/05/06
# copy: (C) Copyright 2014-EOT Cadit Inc., All Rights Reserved.
#------------------------------------------------------------------------------

import textwrap

from aadict import aadict

from ...controller import DescribeController
from ... import test_helpers

#------------------------------------------------------------------------------
class TestNumpydoc(test_helpers.TestHelper):

  #----------------------------------------------------------------------------
  def setUp(self):
    super(TestNumpydoc, self).setUp()
    from ...typereg import TypeRegistry
    self.typereg = TypeRegistry()
    self.context = aadict(options=aadict(
      commentToken=self.typereg.options.commentToken, typereg=self.typereg))

  #----------------------------------------------------------------------------
  def test_FixedNumpyDocString_preserves_empty_lines(self):
    from .extractor import FixedNumpyDocString
    src = '''\
Returns
-------
A paragraph.

A multi-line
paragraph.'''
    self.assertMultiLineEqual(str(FixedNumpyDocString(src)), src)

  #----------------------------------------------------------------------------
  def test_extract_unexpected_sections(self):
    from .extractor import extract
    with self.assertRaises(ValueError) as cm:
      extract(self.context, 'foo\n\nParameters\n----------\n\n(invalid)', '##')
    self.assertEqual(
      str(cm.exception),
      "unexpected/invalid nested section(s): 'Parameters'")

  #----------------------------------------------------------------------------
  def test_extract_dict_one_attribute(self):
    from .extractor import extract
    self.assertEqual(
      extract(self.context, 'prelude\nk1 : s1\n\n', '##'),
      dict(doc='prelude', spec='dict', value=[dict(name='k1', spec='s1')]))

  #----------------------------------------------------------------------------
  def test_extract_dict_two_attributes(self):
    from .extractor import extract
    self.assertEqual(
      extract(self.context, 'prelude\nk1 : s1\nk2 : s2\n', '##'),
      dict(doc='prelude', spec='dict', value=[
        dict(name='k1', spec='s1'),
        dict(name='k2', spec='s2'),
      ]))

  #----------------------------------------------------------------------------
  def test_extract_whitespace_extra(self):
    from .extractor import extract
    self.assertEqual(
      extract(self.context, 'prelude\nk1\t :  s1 \nk2  : s2\n', '##'),
      dict(doc='prelude', spec='dict', value=[
        dict(name='k1', spec='s1'),
        dict(name='k2', spec='s2'),
      ]))

  # TODO: enable this when supported...
  # #----------------------------------------------------------------------------
  # def test_extract_whitespace_agnostic(self):
  #   from .extractor import extract
  #   self.assertEqual(
  #     extract(self.context, 'prelude\nk1\t: s1\nk2\t: s2\n', '##'),
  #     dict(doc='prelude', spec='dict', value=[
  #       dict(name='k1', spec='s1'),
  #       dict(name='k2', spec='s2'),
  #     ]))

  #----------------------------------------------------------------------------
  def test_extract_single_toplevel_anonymous_implicit(self):
    from .extractor import extract
    self.assertEqual(
      extract(self.context, '''\
the prelude
k1 : s1
  d1
k2 : s2
k3 : s3
  d3
''', '##'),
      dict(doc='the prelude', spec='dict', value=[
        dict(name='k1', spec='s1', doc='d1'),
        dict(name='k2', spec='s2'),
        dict(name='k3', spec='s3', doc='d3'),
      ]))

  #----------------------------------------------------------------------------
  def test_extract_single_toplevel_anonymous_explicit(self):
    from .extractor import extract
    self.assertEqual(
      extract(self.context, '''\
the prelude
dict
  inner prelude
  k1 : s1
    d1
  k2 : s2
  k3 : s3
    d3
''', '##'),
      dict(doc='the prelude', spec='oneof', value=[
        dict(spec='dict', doc='inner prelude', value=[
          dict(name='k1', spec='s1', doc='d1'),
          dict(name='k2', spec='s2'),
          dict(name='k3', spec='s3', doc='d3'),
        ])
      ]))

  #----------------------------------------------------------------------------
  def test_extract_single_toplevel_declarative(self):
    from .extractor import extract
    self.assertEqual(
      extract(self.context, '''\
the prelude
KeyMap
  inner prelude
  k1 : s1
    d1
  k2 : s2
  k3 : s3
    d3
''', '##'),
      dict(doc='the prelude', spec='oneof', value=[
        dict(spec='KeyMap', doc='inner prelude', value=[
          dict(name='k1', spec='s1', doc='d1'),
          dict(name='k2', spec='s2'),
          dict(name='k3', spec='s3', doc='d3'),
        ])
      ]))

  #----------------------------------------------------------------------------
  def test_extract_single_namespaced_anonymous(self):
    from .extractor import extract
    self.assertEqual(
      extract(self.context, '''\
the prelude
keymap : dict
  inner prelude
  k1 : s1
    d1
  k2 : s2
  k3 : s3
    d3
''', '##'),
      dict(doc='the prelude', spec='dict', value=[
        dict(name='keymap', spec='dict', doc='inner prelude', value=[
          dict(name='k1', spec='s1', doc='d1'),
          dict(name='k2', spec='s2'),
          dict(name='k3', spec='s3', doc='d3'),
        ])
      ]))

  #----------------------------------------------------------------------------
  def test_extract_single_namespaced_declarative(self):
    from .extractor import extract
    self.assertEqual(
      extract(self.context, '''\
the prelude
keymap : KeyMap
  inner prelude
  k1 : s1
    d1
  k2 : s2
  k3 : s3
    d3
''', '##'),
      dict(doc='the prelude', spec='dict', value=[
        dict(name='keymap', spec='KeyMap', doc='inner prelude', value=[
          dict(name='k1', spec='s1', doc='d1'),
          dict(name='k2', spec='s2'),
          dict(name='k3', spec='s3', doc='d3'),
        ])
      ]))

  #----------------------------------------------------------------------------
  def test_extract_dual_namespaced_declarative(self):
    from .extractor import extract
    self.assertEqual(
      extract(self.context, '''\
the prelude
dict
  inner prelude a
  keymap : KeyMap
    inner prelude a.2
    k1 : s1
      d1
    k2 : s2
    k3 : s3
      d3
dict
  inner prelude b
  othermap : OtherMap
    inner prelude b.2
    k1 : s1
''', '##'),
      dict(doc='the prelude', spec='oneof', value=[
        dict(spec='dict', doc='inner prelude a', value=[
          dict(name='keymap', spec='KeyMap', doc='inner prelude a.2', value=[
            dict(name='k1', spec='s1', doc='d1'),
            dict(name='k2', spec='s2'),
            dict(name='k3', spec='s3', doc='d3'),
          ])]),
        dict(spec='dict', doc='inner prelude b', value=[
          dict(name='othermap', spec='OtherMap', doc='inner prelude b.2', value=[
            dict(name='k1', spec='s1'),
          ])
        ])
      ]))

  #----------------------------------------------------------------------------
  def test_extract_recursive(self):
    from .extractor import extract
    self.assertEqual(
      extract(self.context, '''\
the prelude 1
dict
  inner prelude 2
  keymap : KeyMap
    inner prelude 3
    k3 : s3
      inner prelude 4
      k4 : s4
''', '##'),
      dict(doc='the prelude 1', spec='oneof', value=[
        dict(spec='dict', doc='inner prelude 2', value=[
          dict(name='keymap', spec='KeyMap', doc='inner prelude 3', value=[
            dict(name='k3', spec='s3', doc='inner prelude 4', value=[
              dict(name='k4', spec='s4')
            ])
          ])
        ])
      ]))

  #----------------------------------------------------------------------------
  def test_extract_rst_and_attributes(self):
    from .extractor import extract
    self.assertEqual(
      extract(self.context, '''\
a preamble
with a list:
  * one: 1
  * two
k1 : v1
  d1
''', '##'),
      dict(doc='a preamble\nwith a list:\n    * one: 1\n    * two', spec='dict', value=[
        dict(name='k1', spec='v1', doc='d1'),
      ]))

  #----------------------------------------------------------------------------
  def test_extract_rst_and_oneof(self):
    from .extractor import extract
    self.assertEqual(
      extract(self.context, '''\
a preamble
with a list:
  * one: 1
  * two
dict
  inner prelude 2
  k1 : v1
''', '##'),
      dict(doc='a preamble\nwith a list:\n    * one: 1\n    * two', spec='oneof', value=[
        dict(spec='dict', doc='inner prelude 2', value=[
          dict(name='k1', spec='v1'),
        ])
      ]))

  #----------------------------------------------------------------------------
  def test_extract_httpalias(self):
    from ...typereg import Type, TypeRef
    from .extractor import numpy2type
    self.assertEqual(
      numpy2type(self.context, [
        ('pyramid.httpexceptions.HTTPBadRequest', '', ['', '', 'Invalid request data.'])]),
      ([], TypeRef(doc='Invalid request data.',
                     type=Type(base='dict', name='pyramid.httpexceptions.HTTPBadRequest'))))
    self.assertEqual(
      numpy2type(self.context, [
        ('HTTPBadRequest', '', ['', '', 'Invalid request data.'])]),
      ([], TypeRef(doc='Invalid request data.',
                     type=Type(base='dict', name='HTTPBadRequest'))))

  #----------------------------------------------------------------------------
  def test_extract_entry_doc(self):
    from ...typereg import Type, TypeRef
    from .plugin import parser
    entry = aadict(doc='''

Some entry documentation.

And other
stuff...

Returns
-------

On success, returns a dictionary
with the following attributes:

k1 : V1
k2 : V2
  last big mountain.

Raises
------

All the standard stuff.

HTTPNotFound
  not found, eh?
HTTPForbidden
  not authorized.
''')
    self.assertEqual(
      dict(parser(entry, self.context)),
      dict(
        doc='''\
Some entry documentation.

And other
stuff...

Returns
-------
On success, returns a dictionary
with the following attributes:

Raises
------
All the standard stuff.''',
        params=None,
        returns=Type(base='compound', name='dict', value=[
          TypeRef(name='k1', type=Type(base='dict', name='V1')),
          TypeRef(name='k2', type=Type(base='dict', name='V2'), doc='last big mountain.'),
        ]),
        raises=Type(base='compound', name='oneof', value=[
          TypeRef(type=Type(base='dict', name='HTTPNotFound'), doc='not found, eh?'),
          TypeRef(type=Type(base='dict', name='HTTPForbidden'), doc='not authorized.'),
        ]),
      ))

  #----------------------------------------------------------------------------
  def test_extract_nested(self):
    from ...typereg import Type, TypeRef
    from .plugin import parser
    entry = aadict(doc=textwrap.dedent('''
      Returns
      -------
      shape : Shape
        A shape.
        sides : int, min: 3
          The number of sides.
        source : Source
          A source.
          uri : str
            The URI.
    '''))
    self.assertEqual(
      dict(parser(entry, self.context)),
      dict(
        doc='',
        params=None,
        returns=Type(base='compound', name='dict', value=[
          TypeRef(name='shape', type=
            Type(base='dict', name='Shape', doc='A shape.', value=[
              TypeRef(name='sides', type=Type(base='scalar', name='integer'),
                      params=dict(min=3), doc='The number of sides.'),
              TypeRef(name='source', type=
                Type(base='dict', name='Source', doc='A source.', value=[
                  TypeRef(name='uri', type=Type(base='scalar', name='string'),
                          doc='The URI.'),
                ]))]))]),
        raises=None,
      ))

  #----------------------------------------------------------------------------
  def test_extract_typerefWithParam(self):
    from ...typereg import Type, TypeRef
    from .plugin import parser
    entry = aadict(doc=textwrap.dedent('''
      Returns
      -------
      shape : Shape, default: null
        A shape.
        sides : int
    '''))
    self.assertEqual(
      dict(parser(entry, self.context)),
      dict(
        doc='',
        params=None,
        returns=Type(base='compound', name='dict', value=[
          TypeRef(name='shape', params=dict(default=None, optional=True), type=
            Type(base='dict', name='Shape', doc='A shape.', value=[
              TypeRef(name='sides', type=Type(base='scalar', name='integer')),
            ]))]),
        raises=None,
      ))

  #----------------------------------------------------------------------------
  def test_extract_list_with_schema_and_attribute_comments(self):
    from ...typereg import Type, TypeRef
    from .plugin import parser
    entry = aadict(doc=textwrap.dedent('''
      Returns
      -------
      shape : list(Shape), default: null
        A kind of shape.
        Shape
          A shape.
          sides : int
    '''))
    self.assertEqual(
      dict(parser(entry, self.context)),
      dict(
        doc='',
        params=None,
        returns=Type(base='compound', name='dict', value=[
          TypeRef(name='shape', params=dict(default=None, optional=True),
                  doc='A kind of shape.', type=
            Type(base='compound', name='list', value=
              # note: this is a TypeRef *only* because the `registerTypes`
              #       call in `parser` converts Types to TypeRefs (so it
              #       can be de-referenced later during merging.
              TypeRef(type=
                Type(base='dict', name='Shape', doc='A shape.', value=[
                  TypeRef(name='sides', type=Type(base='scalar', name='integer'))
                ]))))]),
        raises=None,
      ))

  # TODO: implement support for this...
  # #----------------------------------------------------------------------------
  # def test_extract_list_with_schema_and_no_attribute_comments(self):
  #   from ...typereg import Type, TypeRef
  #   from .plugin import parser
  #   entry = aadict(doc=textwrap.dedent('''
  #     Returns
  #     -------
  #     shape : list(Shape), default: null
  #       Shape
  #         A shape.
  #         sides : int
  #   '''))
  #   self.assertEqual(
  #     dict(parser(entry, self.context)),
  #     dict(
  #       doc='',
  #       params=None,
  #       returns=Type(base='compound', name='dict', value=[
  #         TypeRef(name='shape', params=dict(default=None, optional=True),
  #                 type=
  #           Type(base='compound', name='list', value=
  #             # note: this is a TypeRef *only* because the `registerTypes`
  #             #       call in `parser` converts Types to TypeRefs (so it
  #             #       can be de-referenced later during merging.
  #             TypeRef(type=
  #               Type(base='dict', name='Shape', doc='A shape.', value=[
  #                 TypeRef(name='sides', type=Type(base='scalar', name='integer'))
  #               ]))))]),
  #       raises=None,
  #     ))

  #----------------------------------------------------------------------------
  def test_multiextract(self):
    from ...typereg import Type, TypeRef
    from .extractor import extractMultiType
    src = '''
this is doc1.
Type1
  type1 doc.
  foo : int
  bar : Shape
    a shape??
    sides : int
shortstr : str, max: 255
  short string must be short.
evenint : int, limit: even numbers only
  even integral numbers only.
doc2
Type2
  type-dos!
  three : Shape
    a triangle.
'''
    self.assertEqual(
      list(extractMultiType(self.context, src, '##')),
      [
        ('this is doc1.',
         Type(base='dict', name='Type1', doc='type1 doc.', value=[
           TypeRef(name='foo', type=Type(base='scalar', name='integer')),
           TypeRef(name='bar', type=
             Type(base='dict', name='Shape', doc='a shape??', value=[
               TypeRef(name='sides', type=Type(base='scalar', name='integer'))]))])),
        (None,
         Type(base=Type.EXTENSION, name='shortstr', doc='short string must be short.', value=
           TypeRef(type=Type(base='scalar', name='string'), params={'max': 255}))),
        (None,
         Type(base=Type.EXTENSION, name='evenint', doc='even integral numbers only.', value=
           TypeRef(type=Type(base='scalar', name='integer'),
                   params={'limit': 'even numbers only'}))),
        ('doc2',
         Type(base='dict', name='Type2', doc='type-dos!', value=[
           TypeRef(name='three', type=Type(base='dict', name='Shape'), doc='a triangle.')])),
      ])

  #----------------------------------------------------------------------------
  def test_describer_params_scalars(self):
    from pyramid_controllers import RestController, expose
    from ...describer import Describer
    from ...typereg import Type, TypeRef
    class Root(RestController):
      @expose
      def get(self, request):
        '''
        @PUBLIC

        Parameters
        ----------
        solid : bool
          is this root *solid*?
        zen : integer
        ages : list(num)
          a series of ages.
        which1 : ( 'this' | 'that' | 42 )
          which one.
        which2 : ( 'this' | 'that' | 42 ), optional, default: 42
          which two.
        '''
    desc = Describer(settings=dict({'access.control': '*'})).analyze(Root())
    self.assertEqual(
      desc.endpoints[0].methods[0].params,
      Type(base='compound', name='dict', value=[
        TypeRef(name='solid', type=Type(base='scalar', name='boolean'), doc='is this root *solid*?'),
        TypeRef(name='zen', type=Type(base='scalar', name='integer')),
        TypeRef(name='ages', type=Type(
            base='compound', name='list', value=Type(base='scalar', name='number')),
          doc='a series of ages.'),
        TypeRef(name='which1', type=Type(base='compound', name='oneof', value=[
            Type(base='constant', name='string', value='this'),
            Type(base='constant', name='string', value='that'),
            Type(base='constant', name='integer', value=42),
        ]), doc='which one.'),
        TypeRef(name='which2', type=Type(base='compound', name='oneof', value=[
            Type(base='constant', name='string', value='this'),
            Type(base='constant', name='string', value='that'),
            Type(base='constant', name='integer', value=42),
        ]), doc='which two.', params=dict(optional=True, default=42)),
      ]))

  #----------------------------------------------------------------------------
  def test_describer_params_access(self):
    from pyramid_controllers import RestController, expose
    from ...describer import Describer
    from ...typereg import Type, TypeRef
    class Root(RestController):
      @expose
      def get(self, request):
        '''
        @PUBLIC

        Parameters
        ----------
        a1 : str
        a2 : str, read, write, create

        r1 : str, r
        r2 : str, ro
        r3 : str, read-only

        w1 : str, w
        w2 : str, wo
        w3 : str, write-only
        w4 : str, u
        w5 : str, uo
        w6 : str, update-only

        c1 : str, c
        c2 : str, co
        c3 : str, create-only

        b1 : str, rw
        b2 : str, read-write
        b3 : str, read, write
        '''
    StringType = Type(base='scalar', name='string')
    desc = Describer(settings=dict({'access.control': '*'})).analyze(Root())
    self.assertEqual(desc.endpoints[0].methods[0].params.base, 'compound')
    self.assertEqual(desc.endpoints[0].methods[0].params.name, 'dict')
    self.assertEqual(
      desc.endpoints[0].methods[0].params.value,
      [
        TypeRef(name='a1', type=StringType),
        TypeRef(name='a2', type=StringType, params={'read': True, 'write': True, 'create': True}),

        TypeRef(name='r1', type=StringType, params={'read': True}),
        TypeRef(name='r2', type=StringType, params={'read': True, 'write': False, 'create': False}),
        TypeRef(name='r3', type=StringType, params={'read': True, 'write': False, 'create': False}),

        TypeRef(name='w1', type=StringType, params={'write': True, 'create': True}),
        TypeRef(name='w2', type=StringType, params={'read': False, 'write': True, 'create': True}),
        TypeRef(name='w3', type=StringType, params={'read': False, 'write': True, 'create': True}),
        TypeRef(name='w4', type=StringType, params={'write': True, 'create': True}),
        TypeRef(name='w5', type=StringType, params={'read': False, 'write': True, 'create': True}),
        TypeRef(name='w6', type=StringType, params={'read': False, 'write': True, 'create': True}),

        TypeRef(name='c1', type=StringType, params={'create': True}),
        TypeRef(name='c2', type=StringType, params={'read': False, 'write': False, 'create': True}),
        TypeRef(name='c3', type=StringType, params={'read': False, 'write': False, 'create': True}),

        TypeRef(name='b1', type=StringType, params={'read': True, 'write': True, 'create': True}),
        TypeRef(name='b2', type=StringType, params={'read': True, 'write': True, 'create': True}),
        TypeRef(name='b3', type=StringType, params={'read': True, 'write': True, 'create': True}),
      ])

  #----------------------------------------------------------------------------
  def test_describer_params_tree(self):
    from pyramid_controllers import RestController, expose
    from ...describer import Describer
    from ...typereg import Type, TypeRef
    class Root(RestController):
      @expose
      def get(self, request):
        '''
        @PUBLIC

        Parameters
        ----------
        i : int
          an integral
        obj : AnObject
          i believe!
          p1 : T1, optional
          p2 : T2
            best sequel.
        '''
    desc = Describer(settings=dict({'access.control': '*'})).analyze(Root())
    self.assertEqual(
      desc.typereg.types(),
      [
        Type(base='dict', name='AnObject', doc='i believe!', value=[
          TypeRef(name='p1', type=Type(base='dict', name='T1'), params=dict(optional=True)),
          TypeRef(name='p2', type=Type(base='dict', name='T2'), doc='best sequel.'),
        ]),
        Type(base='dict', name='T1'),
        Type(base='dict', name='T2'),
      ])
    self.assertEqual(
      desc.endpoints[0].methods[0].params,
      Type(base='compound', name='dict', value=[
        TypeRef(name='i', type=Type(base='scalar', name='integer'), doc='an integral'),
        TypeRef(name='obj', type=desc.typereg.get('AnObject')),
      ]))

  #----------------------------------------------------------------------------
  def test_merge_doc(self):
    from pyramid_controllers import RestController, expose
    from ...describer import Describer
    from ...typereg import Type, TypeRef
    class Root(RestController):
      @expose
      def put(self, request):
        '''
        @PUBLIC

        Parameters
        ----------
        Shape

          A shape is provided.

          A shape has sides.

          sides : int

        Returns
        -------
        Shape

          A shape is returned.

          A shape has sides.

          sides : int
        '''
    desc = Describer(settings=dict({'access.control': '*'})).analyze(Root())
    ShapeType = desc.typereg.get('Shape')
    self.assertEqual(
      ShapeType,
      Type(
        base  = 'dict',
        name  = 'Shape',
        doc   = 'A shape has sides.',
        value = [
          TypeRef(name='sides', type=Type(base='scalar', name='integer')),
        ]))
    self.assertEquals(
      desc.endpoints[0].methods[0].params,
      TypeRef(type=ShapeType, doc='A shape is provided.'))
    self.assertEquals(
      desc.endpoints[0].methods[0].returns,
      TypeRef(type=ShapeType, doc='A shape is returned.'))

  #----------------------------------------------------------------------------
  def test_doc_can_be_rst(self):
    from pyramid_controllers import RestController, expose
    from ...describer import Describer
    from ...typereg import Type, TypeRef
    class Root(RestController):
      @expose
      def put(self, request):
        '''
        @PUBLIC

        Parameters
        ----------
        Shape

          A shape has sides,
          e.g.:
            * 3: triangle
            * 4: square

          and more.

          sides : int
        '''
    desc = Describer(settings=dict({'access.control': '*'})).analyze(Root())
    ShapeType = desc.typereg.get('Shape')
    self.assertEqual(
      ShapeType,
      Type(
        base  = 'dict',
        name  = 'Shape',
        doc   = 'A shape has sides,\ne.g.:\n    * 3: triangle\n    * 4: square\n\nand more.',
        value = [
          TypeRef(name='sides', type=Type(base='scalar', name='integer')),
        ]))

  #----------------------------------------------------------------------------
  def test_describer_params_merge_attributes(self):
    from pyramid_controllers import RestController, expose
    from ...describer import Describer
    from ...typereg import Type, TypeRef
    class Root(RestController):
      @expose
      def put(self, request):
        '''
        @PUBLIC

        Parameters
        ----------
        Shape
          sides : int
          hidden : bool

        Returns
        -------
        Shape
          sides : int
          created : num
        '''
    desc = Describer(settings=dict({'access.control': '*'})).analyze(Root())
    ShapeType = desc.typereg.get('Shape')
    self.assertEqual(
      ShapeType,
      Type(base='dict', name='Shape', value=[
        TypeRef(name='created', type=Type(base='scalar', name='number'),
                params={'read': True}),
        TypeRef(name='hidden', type=Type(base='scalar', name='boolean'),
                params={'write': True, 'create': True}),
        TypeRef(name='sides', type=Type(base='scalar', name='integer')),
      ]))
    self.assertIs(desc.endpoints[0].methods[0].params, ShapeType)
    self.assertIs(desc.endpoints[0].methods[0].returns, ShapeType)

  #----------------------------------------------------------------------------
  def test_describer_params_merge_attributes_namespaced(self):
    from pyramid_controllers import RestController, expose
    from ...describer import Describer
    from ...typereg import Type, TypeRef
    class Root(RestController):
      @expose
      def put(self, request):
        '''
        @PUBLIC

        Parameters
        ----------
        update : Shape
          sides : int
          hidden : bool

        Returns
        -------
        dict
          result : Shape
            sides : int
            created : num
        '''
    desc = Describer(settings=dict({'access.control': '*'})).analyze(Root())
    ShapeType = desc.typereg.get('Shape')
    self.assertEqual(
      ShapeType,
      Type(base='dict', name='Shape', value=[
        TypeRef(name='created', type=Type(base='scalar', name='number'),
                params={'read': True}),
        TypeRef(name='hidden', type=Type(base='scalar', name='boolean'),
                params={'write': True, 'create': True}),
        TypeRef(name='sides', type=Type(base='scalar', name='integer')),
      ]))
    self.assertEqual(
      desc.endpoints[0].methods[0].params,
      Type(base='compound', name='dict', value=[
        TypeRef(name='update', type=ShapeType)]))
    self.assertEqual(
      desc.endpoints[0].methods[0].returns,
      Type(base='compound', name='dict', value=[
        TypeRef(name='result', type=ShapeType)]))
    self.assertIs(desc.endpoints[0].methods[0].params.value[0].type, ShapeType)
    self.assertIs(desc.endpoints[0].methods[0].returns.value[0].type, ShapeType)

  #----------------------------------------------------------------------------
  def test_describer_params_merge_reference_returns(self):
    from pyramid_controllers import RestController, expose
    from ...describer import Describer
    from ...typereg import Type, TypeRef
    class Root(RestController):
      @expose
      def put(self, request):
        '''
        @PUBLIC

        Parameters
        ----------
        Shape
          sides : int
          hidden : bool, wo

        Returns
        -------
        Shape
        '''
    desc = Describer(settings=dict({'access.control': '*'})).analyze(Root())
    self.assertEqual(
      desc.endpoints[0].methods[0].params,
      Type(base='dict', name='Shape', value=[
        TypeRef(name='sides', type=Type(base='scalar', name='integer')),
        TypeRef(name='hidden', type=Type(base='scalar', name='boolean'),
                params={'read': False, 'write': True, 'create': True}),
      ]))
    self.assertEqual(
      desc.endpoints[0].methods[0].returns,
      Type(base='dict', name='Shape', value=[
        TypeRef(name='sides', type=Type(base='scalar', name='integer')),
        TypeRef(name='hidden', type=Type(base='scalar', name='boolean'),
                params={'read': False, 'write': True, 'create': True}),
      ]))

  #----------------------------------------------------------------------------
  def test_describer_params_merge_reference_params(self):
    from pyramid_controllers import RestController, expose
    from ...describer import Describer
    from ...typereg import Type, TypeRef
    class Root(RestController):
      @expose
      def put(self, request):
        '''
        @PUBLIC

        Parameters
        ----------
        Shape

        Returns
        -------
        Shape
          sides : int
          hidden : bool, wo
        '''
    desc = Describer(settings=dict({'access.control': '*'})).analyze(Root())
    self.assertEqual(
      desc.endpoints[0].methods[0].params,
      Type(base='dict', name='Shape', value=[
        TypeRef(name='sides', type=Type(base='scalar', name='integer')),
        TypeRef(name='hidden', type=Type(base='scalar', name='boolean'),
                params={'read': False, 'write': True, 'create': True}),
      ]))
    self.assertEqual(
      desc.endpoints[0].methods[0].returns,
      Type(base='dict', name='Shape', value=[
        TypeRef(name='sides', type=Type(base='scalar', name='integer')),
        TypeRef(name='hidden', type=Type(base='scalar', name='boolean'),
                params={'read': False, 'write': True, 'create': True}),
      ]))

  #----------------------------------------------------------------------------
  def test_typereg_http_autoload(self):
    from pyramid_controllers import RestController, expose
    from ...describer import Describer
    from ...typereg import Type, TypeRef
    class Root(RestController):
      @expose
      def get(self, request):
        '''
        @PUBLIC

        Raises
        ------
        HTTPForbidden          ## a random comment
          no sirree bob!       ## another comment
        '''
    desc = Describer(settings=dict({'access.control': '*'})).analyze(Root())
    http403 = desc.typereg.get('HTTPForbidden')
    self.assertEqual(
      desc.endpoints[0].methods[0].raises,
      TypeRef(type=http403, doc='no sirree bob!'))
    chk = Type(
      base  = 'dict',
      name  = 'HTTPForbidden',
      doc   = 'Access was denied to this resource.',
      value = [
        TypeRef(name='code', type=Type(base='constant', name='integer', value=403)),
        TypeRef(name='message', type=Type(base='constant', name='string', value='Forbidden')),
      ])
    self.assertEqual(http403, chk)

  #----------------------------------------------------------------------------
  def test_returns_unstructured(self):
    from pyramid_controllers import RestController, expose
    class UnstructuredReturnsRoot(RestController):
      @expose
      def get(self, request):
        '''
        @PUBLIC

        Get's the root.

        Returns
        -------

        The root is simply a JSON structure.
        '''
    root = UnstructuredReturnsRoot()
    root.desc = DescribeController(
      root, doc='URL tree description.',
      settings={
        'formats'        : 'rst',
        'index-redirect' : 'false',
        'exclude'        : ('|^/desc(/.*)?$|'),
        'format.request' : 'true',
      })
    #&showRest=false&showInfo=false
    #&showMeta=false
    self.assertResponse(
      self.send(root, '/desc?showLegend=false&rstMax=true&showMeta=false'),
      200, '''\
.. title:: Contents of "/"

.. class:: contents

.. _`section-contents`:

===============
Contents of "/"
===============

.. class:: endpoints

.. _`section-endpoints`:

---------
Endpoints
---------

.. class:: doc-public endpoint

.. _`endpoint-2f`:

``````
\/
``````

.. class:: methods

.. _`methods-endpoint-2f`:

:::::::
Methods
:::::::

.. class:: doc-public method

.. _`method-2f-474554`:

''\''\''
GET
''\''\''

@PUBLIC

Get's the root.

.. class:: returns

.. _`returns-method-2f-474554`:

"""""""
Returns
"""""""

The root is simply a JSON structure.
''')

  #----------------------------------------------------------------------------
  def test_returns_structured(self):
    from pyramid_controllers import RestController, expose
    class StructuredReturnsRoot(RestController):
      @expose
      def get(self, request):
        '''
        @PUBLIC

        Get's the root.

        Returns
        -------

        Root

          @PUBLIC

          The root.

          solid : bool
            is this root *solid*?
        '''
    root = StructuredReturnsRoot()
    root.desc = DescribeController(
      root, doc='URL tree description.',
      settings={
        'formats'        : 'rst',
        'index-redirect' : 'false',
        'exclude'        : ('|^/desc(/.*)?$|'),
        'format.request' : 'true',
      })
    #&showRest=false&showInfo=false
    #&showMeta=false
    self.assertResponse(
      self.send(root, '/desc?showLegend=false&rstMax=true&showMeta=false'),
      200, '''\
.. title:: Contents of "/"

.. class:: contents

.. _`section-contents`:

===============
Contents of "/"
===============

.. class:: endpoints

.. _`section-endpoints`:

---------
Endpoints
---------

.. class:: doc-public endpoint

.. _`endpoint-2f`:

``````
\/
``````

.. class:: methods

.. _`methods-endpoint-2f`:

:::::::
Methods
:::::::

.. class:: doc-public method

.. _`method-2f-474554`:

''\''\''
GET
''\''\''

@PUBLIC

Get's the root.

.. class:: returns

.. _`returns-method-2f-474554`:

"""""""
Returns
"""""""

.. class:: return

.. _`return-method-2f-474554-526f6f74`:

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
`Root <#typereg-type-526f6f74>`__
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. class:: typereg

.. _`section-typereg`:

------
Types
------

.. class:: doc-public typereg-type

.. _`typereg-type-526f6f74`:

``````
Root
``````

@PUBLIC

The root.

.. class:: attr

::::::
solid
::::::

.. class:: spec

boolean

is this root *solid*?
''')

  #----------------------------------------------------------------------------
  def test_returns_merged(self):
    from pyramid_controllers import RestController, expose
    class MergedReturnsRoot(RestController):
      @expose
      def get(self, request):
        '''
        @PUBLIC

        Get's the root.

        Returns
        -------

        The root is simply a JSON structure.

        Root

          @PUBLIC

          The root.

          solid : bool
            is this root solid?

        Raises
        ------

        HTTPForbidden
          Access denied.

        '''
    root = MergedReturnsRoot()
    root.desc = DescribeController(
      root, doc='URL tree description.',
      settings={
        'formats'        : 'rst',
        'index-redirect' : 'false',
        'exclude'        : ('|^/desc(/.*)?$|'),
        'format.request' : 'true',
      })
    #&showRest=false&showInfo=false
    #&showMeta=false
    self.assertResponse(
      self.send(root, '/desc?showLegend=false&rstMax=true&showMeta=false'),
      200, '''\
.. title:: Contents of "/"

.. class:: contents

.. _`section-contents`:

===============
Contents of "/"
===============

.. class:: endpoints

.. _`section-endpoints`:

---------
Endpoints
---------

.. class:: doc-public endpoint

.. _`endpoint-2f`:

``````
\/
``````

.. class:: methods

.. _`methods-endpoint-2f`:

:::::::
Methods
:::::::

.. class:: doc-public method

.. _`method-2f-474554`:

''\''\''
GET
''\''\''

@PUBLIC

Get's the root.

.. class:: returns

.. _`returns-method-2f-474554`:

"""""""
Returns
"""""""

The root is simply a JSON structure.

.. class:: return

.. _`return-method-2f-474554-526f6f74`:

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
`Root <#typereg-type-526f6f74>`__
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. class:: raises

.. _`raises-method-2f-474554`:

""""""
Raises
""""""

.. class:: raise

.. _`raise-method-2f-474554-48545450466f7262696464656e`:

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
`HTTPForbidden <#typereg-type-48545450466f7262696464656e>`__
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Access denied.

.. class:: typereg

.. _`section-typereg`:

------
Types
------

.. class:: source-pyramid-httpexceptions typereg-type

.. _`typereg-type-48545450466f7262696464656e`:

`````````````
HTTPForbidden
`````````````

Access was denied to this resource.

.. class:: attr

::::::
code
::::::

.. class:: spec

``403``

.. class:: attr

:::::::
message
:::::::

.. class:: spec

``"Forbidden"``

.. class:: doc-public typereg-type

.. _`typereg-type-526f6f74`:

``````
Root
``````

@PUBLIC

The root.

.. class:: attr

::::::
solid
::::::

.. class:: spec

boolean

is this root solid?
''')

  #----------------------------------------------------------------------------
  def test_rst(self):
    from ...test.syntax_numpydoc import Root
    root = Root()
    root.desc = DescribeController(
      root, doc='URL tree description.',
      settings={
        'formats'        : 'rst',
        'index-redirect' : 'false',
        'exclude'        : ('|^/desc(/.*)?$|'),
        'format.request' : 'true',
      })
    #&showRest=false&showInfo=false
    #&showMeta=false

    self.send(root, '/desc?showLegend=false&rstMax=true&showMeta=false')

    # self.assertResponse(
    #   self.send(root, '/desc?showLegend=false&rstMax=true&showMeta=false'),
    #   200, self.loadTestData('syntax_numpydoc.output.rst'))

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
