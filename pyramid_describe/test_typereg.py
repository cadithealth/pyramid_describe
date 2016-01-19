# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2015/12/02
# copy: (C) Copyright 2015-EOT Cadit Inc., All Rights Reserved.
#------------------------------------------------------------------------------

import unittest
import json
import textwrap

import six
from aadict import aadict
from pyramid_controllers.test_helpers import TestHelper
import pxml

#------------------------------------------------------------------------------
class TestTypeRegistry(TestHelper, pxml.XmlTestMixin):

  #----------------------------------------------------------------------------
  def parse(self, spec, *args, **kw):
    from .typereg import TypeRegistry
    return TypeRegistry(*args, **kw).parseType(spec)

  #----------------------------------------------------------------------------
  def parsePartial(self, spec, *args, **kw):
    from .typereg import TypeRegistry
    return TypeRegistry(*args, **kw).parseType(spec, complete=False)

  #----------------------------------------------------------------------------
  def test_parseType_scalar(self):
    self.assertEqual(repr(self.parse('any')),      '<Type scalar:any>')
    self.assertEqual(repr(self.parse('byte')),     '<Type scalar:byte>')
    self.assertEqual(repr(self.parse('bytes')),    '<Type scalar:bytes>')
    self.assertEqual(repr(self.parse('boolean')),  '<Type scalar:boolean>')
    self.assertEqual(repr(self.parse('integer')),  '<Type scalar:integer>')
    self.assertEqual(repr(self.parse('number')),   '<Type scalar:number>')
    self.assertEqual(repr(self.parse('string')),   '<Type scalar:string>')

  #----------------------------------------------------------------------------
  def test_parseType_scalar_aliases(self):
    self.assertEqual(repr(self.parse('bool')),     '<Type scalar:boolean>')
    self.assertEqual(repr(self.parse('int')),      '<Type scalar:integer>')
    self.assertEqual(repr(self.parse('num')),      '<Type scalar:number>')
    self.assertEqual(repr(self.parse('str')),      '<Type scalar:string>')
    self.assertEqual(
      repr(self.parse('null | byte | bytes | bool | 13 | 4.5 | int | num | str')),
      '<Type compound:oneof value=['
      '<Type constant:null value=None>'
      ', <Type scalar:byte>'
      ', <Type scalar:bytes>'
      ', <Type scalar:boolean>'
      ', <Type constant:integer value=13>'
      ', <Type constant:number value=4.5>'
      ', <Type scalar:integer>'
      ', <Type scalar:number>'
      ', <Type scalar:string>]>'
    )
    self.assertEqual(
      repr(self.parse('list(int)')),
      '<Type compound:list value=<Type scalar:integer>>')
    self.assertEqual(repr(self.parse('none')),     '<Type constant:null value=None>')
    self.assertEqual(repr(self.parse('None')),     '<Type constant:null value=None>')
    self.assertEqual(repr(self.parse('NIL')),      '<Type constant:null value=None>')

  #----------------------------------------------------------------------------
  def test_parseType_compound_oneof(self):
    self.assertEqual(
      repr(self.parse('byte | bytes')),
      '<Type compound:oneof value=[<Type scalar:byte>, <Type scalar:bytes>]>')
    self.assertEqual(
      repr(self.parse(' ( byte | bytes ) ')),
      '<Type compound:oneof value=[<Type scalar:byte>, <Type scalar:bytes>]>')
    self.assertEqual(
      repr(self.parse('null | byte | bytes | boolean | 13 | 4.5 | integer | number | string')),
      '<Type compound:oneof value=['
      '<Type constant:null value=None>'
      ', <Type scalar:byte>'
      ', <Type scalar:bytes>'
      ', <Type scalar:boolean>'
      ', <Type constant:integer value=13>'
      ', <Type constant:number value=4.5>'
      ', <Type scalar:integer>'
      ', <Type scalar:number>'
      ', <Type scalar:string>]>'
    )
    self.assertEqual(
      repr(self.parse(''' ( 'm' | 'f' | 'o' ) ''')),
      '<Type compound:oneof value=['
      '<Type constant:string value=\'m\'>'
      ', <Type constant:string value=\'f\'>'
      ', <Type constant:string value=\'o\'>]>')

  #----------------------------------------------------------------------------
  def test_parseType_compound_union(self):
    self.assertEqual(
      repr(self.parse('int & num')),
      '<Type compound:union value=[<Type scalar:integer>, <Type scalar:number>]>')
    self.assertEqual(
      repr(self.parse(' ( int & num ) ')),
      '<Type compound:union value=[<Type scalar:integer>, <Type scalar:number>]>')

  #----------------------------------------------------------------------------
  def test_parseType_compound_list(self):
    self.assertEqual(repr(self.parse('list')),            '<Type compound:list>')
    self.assertEqual(repr(self.parse('list(any)')),       '<Type compound:list value=<Type scalar:any>>')
    self.assertEqual(repr(self.parse(' list ( any ) ')),  '<Type compound:list value=<Type scalar:any>>')
    self.assertEqual(repr(self.parse('list(integer)')),   '<Type compound:list value=<Type scalar:integer>>')
    self.assertEqual(
      repr(self.parse('list( null | integer )')),
      '<Type compound:list value=<Type compound:oneof value=['
      '<Type constant:null value=None>, <Type scalar:integer>]>>')

  #----------------------------------------------------------------------------
  def test_parseType_compound_ref(self):
    self.assertEqual(repr(self.parse(' ref ')),           '<Type compound:ref>')
    self.assertEqual(repr(self.parse(' ref ( any ) ')),   '<Type compound:ref value=<Type scalar:any>>')
    self.assertEqual(repr(self.parse('ref(RefType)')),    '<Type compound:ref value=<Type dict:RefType>>')
    self.assertEqual(repr(self.parse('ref ( RefType) ')), '<Type compound:ref value=<Type dict:RefType>>')

  #----------------------------------------------------------------------------
  def test_parseType_compound_custom(self):
    self.assertEqual(repr(self.parse('CustomType')),     '<Type dict:CustomType>')
    self.assertEqual(repr(self.parse(' CustomType ')),   '<Type dict:CustomType>')

  #----------------------------------------------------------------------------
  def test_parseType_constants(self):
    self.assertEqual(repr(self.parse('null')),       '<Type constant:null value=None>')
    self.assertEqual(repr(self.parse('true')),       '<Type constant:boolean value=True>')
    self.assertEqual(repr(self.parse('13')),         '<Type constant:integer value=13>')
    self.assertEqual(repr(self.parse('13.8')),       '<Type constant:number value=13.8>')
    self.assertEqual(repr(self.parse('"foo1"')),     '<Type constant:string value=\'foo1\'>')
    self.assertEqual(repr(self.parse("'foo2'")),     '<Type constant:string value=\'foo2\'>')
    if six.PY2:
      self.assertEqual(repr(self.parse('0x62')),     '<Type constant:byte value=\'b\'>')
      self.assertEqual(repr(self.parse('0x626172')), '<Type constant:bytes value=\'bar\'>')
    else:
      self.assertEqual(repr(self.parse('0x62')),     '<Type constant:byte value=b\'b\'>')
      self.assertEqual(repr(self.parse('0x626172')), '<Type constant:bytes value=b\'bar\'>')
    self.assertEqual(
      repr(self.parse('{"k1": \'v1\', \'k2\': "v2"}')),
      "<Type constant:dict value={'k1': 'v1', 'k2': 'v2'}>"),
    self.assertEqual(
      repr(self.parse('{k1: v1, k2: v2, k3: v3}')),
      "<Type constant:dict value={'k1': 'v1', 'k2': 'v2', 'k3': 'v3'}>"),
    self.assertEqual(
      repr(self.parse('("m" | "f")')),
      '<Type compound:oneof value=['
        '<Type constant:string value=\'m\'>, '
        '<Type constant:string value=\'f\'>]>')

  #----------------------------------------------------------------------------
  def test_parseType_comments(self):
    self.assertEqual(
      repr(self.parse('string ## nada')),
      '<Type scalar:string>')
    self.assertEqual(
      repr(self.parse('list(int|string|43.5) ## nada')),
      '<Type compound:list value=<Type compound:oneof value=['
      '<Type scalar:integer>, '
      '<Type scalar:string>, '
      '<Type constant:number value=43.5>]>>')

  #----------------------------------------------------------------------------
  def test_parseType_incomplete(self):
    # self.assertEqual(
    #   repr(self.parsePartial('integer, default: 50')),
    #   '(<Type scalar:integer>, \', default: 50\')')
    self.assertEqual(
      repr(self.parsePartial('("m" | "f"), not-empty, default: null')),
      '(<Type compound:oneof value=['
         '<Type constant:string value=\'m\'>, '
         '<Type constant:string value=\'f\'>]>, '
        '\', not-empty, default: null\')')

  #----------------------------------------------------------------------------
  def test_anonymous(self):
    from pyramid_controllers import RestController, expose
    from .controller import DescribeController
    class PersonController(RestController):
      @expose
      def get(self, request):
        '''
        @PUBLIC

        Returns the current person.

        :Returns:

        dict
          name : str
            the name
          gender : ( 'm' | 'f' | 'o' )
            gender - male/female/other
          active : bool, read-only
            the enabled state
        '''

      @expose
      def put(self, request):
        '''
        @PUBLIC

        Update the current person.

        :Parameters:

        name : str
          the name
        gender : ( 'm' | 'f' | 'o' )
          gender - male/female/other
        address : dict
          where does this person live?
          line1 : str
          line2 : str, optional
            the second line
          pocode : str
      '''

    root = PersonController()
    root.desc = DescribeController(
      root,
      settings={
        'format.request': 'true',
        'index-redirect': 'false',
        'exclude': '|^/desc(/.*)?$|',
        })

    self.assertResponse(self.send(root, '/desc/application.txt?ascii=true'), 200, '''\
/
|-- <GET>    # @PUBLIC Returns the current person.
`-- <PUT>    # @PUBLIC Update the current person.
''')

  #----------------------------------------------------------------------------
  def test_config_aliases(self):
    from pyramid_controllers import RestController, expose
    from .describer import Describer
    from .typereg import Type, TypeRef
    class Root(RestController):
      @expose
      def get(self, request):
        '''
        @PUBLIC

        Parameters
        ----------
        ShapeReq
          sides : int

        Returns
        -------
        ShapeRes
          sides : int
          created : num
        '''
    desc = Describer(settings={
      'typereg.alias.module.Shape' : 'ShapeReq ShapeRes',
    }).analyze(Root())
    self.assertEqual(
      desc.typereg.types(),
      [
        Type(
          base  = 'dict',
          name  = 'module.Shape',
          value = [
            TypeRef(name='created', type=Type(base='scalar', name='number')),
            TypeRef(name='sides', type=Type(base='scalar', name='integer')),
          ])
      ])
    shape = desc.typereg.get('module.Shape')
    self.assertIs(desc.endpoints[0].methods[0].params, shape)
    self.assertIs(desc.endpoints[0].methods[0].returns, shape)

  #----------------------------------------------------------------------------
  def test_type_object_operators(self):
    from .typereg import Type, TypeRef
    self.assertEqual(
      Type(base='dict', name='foo').__cmp__(Type(base='dict', name='foo')), 0)
    self.assertEqual(
      Type(base='dict', name='foo').__cmp__(Type(base='dict', name='bar')), 1)
    self.assertTrue(
      Type(base='dict', name='foo') == Type(base='dict', name='foo'))
    self.assertFalse(
      Type(base='dict', name='foo') != Type(base='dict', name='foo'))
    self.assertFalse(
      Type(base='dict', name='foo') == Type(base='dict', name='BAR'))
    self.assertTrue(
      Type(base='dict', name='foo') != Type(base='dict', name='BAR'))
    # `meta` should not affect equality...
    self.assertTrue(
      Type(name='foo', meta={'x': 'y'}) == Type(name='foo'))

  #----------------------------------------------------------------------------
  def test_extensions_with_comments(self):
    # todo: this should really be moved into:
    #         pyramid_describe/syntax/numpydoc/test_parser.py
    #       since it is really a test of commenting...
    ext = '''\
      ## this is a comment
      this is ignored documentation.
      epoch : num
        seconds since 1970/1/1.
      ## isodate : (str|epoch), format: YYYY-MM-DDTHH:MM:SS[.MMM]Z
      ##   a timestamp.
      ## Shape
      ##   a regular polygon.
      ##   sides : int, min: 3
    '''
    from .typereg import TypeRegistry, Type, TypeRef
    treg = TypeRegistry(options=aadict(aliases={}))
    self.assertEqual(treg._autotypes, {})
    treg.loadExtensionString(ext)
    self.assertEqual(treg._autotypes, {
      'epoch' : Type(
        base='extension', name='epoch', doc='seconds since 1970/1/1.',
        value=TypeRef(type=Type(base='scalar', name='number'))),
    })

  #----------------------------------------------------------------------------
  def test_extensions_load_multiple(self):
    ext = '''\
      ## this is a comment
      this is ignored documentation.
      epoch : num
        seconds since 1970/1/1.
      isodate : (str|epoch), format: YYYY-MM-DDTHH:MM:SS[.MMM]Z
        a timestamp.
      Shape
        a regular polygon.
        sides : int, min: 3
    '''
    from .typereg import TypeRegistry, Type, TypeRef
    treg = TypeRegistry(options=aadict(aliases={}))
    self.assertEqual(treg._autotypes, {})
    treg.loadExtensionString(ext)
    self.assertEqual(treg._autotypes, {
      'epoch' : Type(
        base='extension', name='epoch', doc='seconds since 1970/1/1.',
        value=TypeRef(type=Type(base='scalar', name='number'))),
      'isodate' : Type(
        base='extension', name='isodate', doc='a timestamp.',
        value=TypeRef(type=Type(base='compound', name='oneof', value=[
            Type(base='scalar', name='string'),
            Type(
              base='extension', name='epoch', doc='seconds since 1970/1/1.',
              value=TypeRef(type=Type(base='scalar', name='number'))),
          ]), params=dict(format='YYYY-MM-DDTHH:MM:SS[.MMM]Z'))),
      'Shape' : Type(
        base='dict', name='Shape', doc='a regular polygon.', value=[
          TypeRef(
            name='sides', type=Type(base='scalar', name='integer'),
            params=dict(min=3))
        ]),
    })

  #----------------------------------------------------------------------------
  def test_extensions_invalid_reference(self):
    ext = '''\
      isodate : (str|epoch)
        a timestamp.
    '''
    from .typereg import TypeRegistry, Type, TypeRef
    treg = TypeRegistry(options=aadict(aliases={}))
    with self.assertRaises(ValueError) as cm:
      treg.loadExtensionString(ext)
    self.assertEqual(
      str(cm.exception),
      'invalid reference to unknown/undefined type "epoch"')

  #----------------------------------------------------------------------------
  def test_extensions_load_only_referenced(self):
    from pyramid_controllers import RestController, expose
    from .describer import Describer
    from .typereg import TypeRegistry, Type, TypeRef
    class Root(RestController):
      @expose
      def get(self, request):
        '''
        @PUBLIC

        Returns
        -------
        created : epoch
        '''
    desc = Describer(settings={
      'typereg.aliases': TypeRegistry.DEFAULT_ALIASES,
      'typereg.extensions':
        'pyramid_describe:extension/epoch.rst'
        + ' pyramid_describe:extension/isodate.rst',
    }).analyze(Root())
    epochchk = Type(
      base     = 'extension',
      name     = 'epoch',
      value    = TypeRef(
        type     = Type(base='scalar', name='number'),
        # todo: this params(scale=6) should really be json-parsed
        # so that it becomes a true int...
        params   = {'scale': 6}),
      doc      = textwrap.dedent('''\
        An `epoch` is a timestamp that is defined as being the number of
        seconds since January 1, 1970 at 00:00:00 UTC. Although the value
        can be any positive or negative decimal number, precision beyond
        nanoseconds may be truncated and/or ignored.'''))
    self.assertEqual(desc.typereg._types.keys(), ['epoch'])
    self.assertEqual(desc.typereg._autotypes.keys(), ['epoch', 'isodate'])
    chk = Type(base='compound', name='dict', value=[
      TypeRef(name='created', type=epochchk)])
    self.assertEqual(desc.endpoints[0].methods[0].returns, chk)

# <Type compound:dict value=[<TypeRef created=<Type unknown:epoch>>]>
# <Type compound:dict value=[<TypeRef created=<Type extension:epoch value=<TypeRef <Type scalar:number> params={'scale': 6}> doc='An `epoch` is a timestamp that is defined as being the number of\nseconds since January 1, 1970 at 00:00:00 UTC. Although the value\ncan be any positive or negative decimal number, precision beyond\nnanoseconds may be truncated and/or ignored.'>>]>


  #----------------------------------------------------------------------------
  def test_clone(self):
    from .typereg import TypeRegistry, Type, TypeRef
    old = TypeRegistry()
    old.addAlias('bigint', 'integer')
    old.registerType(Type(base='dict', name='Shape', doc='A shape.'))
    old.registerType(Type(base='dict', name='Surface', doc='(old)', value=[
      TypeRef(name='shape', type=old.get('Shape'))]))
    new = old.clone()
    new.addAlias('short', 'integer')
    new.registerType(Type(base='dict', name='Shape', doc='A new shape.'))
    new.get('Surface').doc = '(new)'
    self.assertEqual(old.resolveAliases('bigint'), 'integer')
    self.assertEqual(new.resolveAliases('bigint'), 'integer')
    self.assertEqual(old.resolveAliases('short'),  'short')
    self.assertEqual(new.resolveAliases('short'),  'integer')
    self.assertEqual(old.get('Shape').doc, 'A shape.')
    self.assertEqual(new.get('Shape').doc, 'A new shape.')
    self.assertEqual(old.get('Surface').doc, '(old)')
    self.assertEqual(new.get('Surface').doc, '(new)')

#------------------------------------------------------------------------------
# end of $Id$
# $ChangeLog$
#------------------------------------------------------------------------------
