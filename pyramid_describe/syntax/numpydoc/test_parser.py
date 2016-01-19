# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2016/01/16
# copy: (C) Copyright 2016-EOT Cadit Inc., All Rights Reserved.
#------------------------------------------------------------------------------

import unittest

from aadict import aadict

from ...controller import DescribeController
from ...typereg import TypeRegistry, Type, TypeRef
from ... import test_helpers

#------------------------------------------------------------------------------
class TestParsere(unittest.TestCase):

  maxDiff = None

  #----------------------------------------------------------------------------
  def test_parse_dict_anonymous(self):
    from .parser import parse
    src =  '''\
      A shape.
      sides : int, min: 3
        The number of sides.
      created : num
        Creation timestamp.
    '''
    self.assertEqual(
      parse(src),
      ('A shape.',
        Type(base='compound', name='dict', value=[
          TypeRef(name='sides', doc='The number of sides.',
            type=Type(base='scalar', name='integer'),
            params=dict(min=3)),
          TypeRef(name='created', doc='Creation timestamp.',
            type=Type(base='scalar', name='number'),
          )])))

  #----------------------------------------------------------------------------
  def test_parse_dict_named(self):
    from .parser import parse
    src =  '''\
      some doc.
      Shape
        A shape.
        sides : int, min: 3
          The number of sides.
        created : num
          Creation timestamp.
    '''
    self.assertEqual(
      parse(src),
      ('some doc.',
        Type(base='dict', name='Shape', doc='A shape.', value=[
          TypeRef(name='sides', doc='The number of sides.',
            type=Type(base='scalar', name='integer'),
            params=dict(min=3)),
          TypeRef(name='created', doc='Creation timestamp.',
            type=Type(base='scalar', name='number'),
          )])))

  # # todo: enable when implemented...
  # #----------------------------------------------------------------------------
  # def test_parse_list_with_multi_types(self):
  #   # todo: generalize this to handle anything (and any number of)
  #   #       compound types that could support sub-definition. eg:
  #   #
  #   #         things : list(Triangle | Square)
  #   #           a list of either triangles or squares.
  #   #           Triangle
  #   #             A 3-sided Shape.
  #   #             sides : 3
  #   #           Square
  #   #             A 4-sided Shape.
  #   #             sides : 4

  #----------------------------------------------------------------------------
  def test_parseMulti_standalone_single(self):
    from .parser import Parser
    src =  'Shape'
    self.assertEqual(
      list(Parser().parseMulti(src, eager=True)),
      [(None, Type(base='dict', name='Shape'))])

  #----------------------------------------------------------------------------
  def test_parseMulti_standalone_multi(self):
    from .parser import Parser
    src =  'either Shape or Box.\nZoo\n\nShape\n\nBox'
    self.assertEqual(
      list(Parser().parseMulti(src, eager=True)),
      [
        ('either Shape or Box.\nZoo', Type(base='dict', name='Shape')),
        (None, Type(base='dict', name='Box')),
      ])

  #----------------------------------------------------------------------------
  def test_parse_unexpected_sections(self):
    from .parser import parse
    with self.assertRaises(ValueError) as cm:
      parse('foo\n\nParameters\n----------\n\n(invalid)')
    self.assertEqual(
      str(cm.exception),
      "unexpected/invalid nested section(s): 'Parameters'")

  #----------------------------------------------------------------------------
  def test_parse_dict_one_attribute(self):
    from .parser import parse
    self.assertEqual(
      parse('prelude\nk1 : s1\n\n'),
      ('prelude',
        Type(base='compound', name='dict', value=[
          TypeRef(name='k1', type=Type(base='unknown', name='s1'))])))

  #----------------------------------------------------------------------------
  def test_parse_dict_two_attributes(self):
    from .parser import parse
    self.assertEqual(
      parse('prelude\nk1 : s1\nk2 : s2\n'),
      ('prelude',
        Type(base='compound', name='dict', value=[
          TypeRef(name='k1', type=Type(base='unknown', name='s1')),
          TypeRef(name='k2', type=Type(base='unknown', name='s2'))])))

  #----------------------------------------------------------------------------
  def test_parse_whitespace_extra(self):
    from .parser import parse
    self.assertEqual(
      parse('prelude\nk1\t :  s1 \nk2  : s2\n'),
      ('prelude',
        Type(base='compound', name='dict', value=[
          TypeRef(name='k1', type=Type(base='unknown', name='s1')),
          TypeRef(name='k2', type=Type(base='unknown', name='s2'))])))

  #----------------------------------------------------------------------------
  def test_parse_custom_without_value_documents_attribute(self):
    from .parser import parse
    self.assertEqual(
      parse('''\
        prelude
        keymap : KeyMap
          keymap attr doc
        othermap : OtherMap
          OtherMap doc
          attr : type
      '''),
      ('prelude',
        Type(base='compound', name='dict', value=[
          TypeRef(name='keymap', doc='keymap attr doc', type=
            Type(base='dict', name='KeyMap')),
          TypeRef(name='othermap', type=
            Type(base='dict', name='OtherMap', doc='OtherMap doc', value=[
              TypeRef(name='attr', type=Type(base='unknown', name='type')),
            ]))])))

  #----------------------------------------------------------------------------
  def test_parse_single_toplevel_anonymous_implicit(self):
    from .parser import parse
    self.assertEqual(
      parse('''\
        the prelude
        k1 : s1
          d1
        k2 : s2
        k3 : s3
          d3
      '''),
      ('the prelude',
        Type(base='compound', name='dict', value=[
          TypeRef(name='k1', type=Type(base='unknown', name='s1'), doc='d1'),
          TypeRef(name='k2', type=Type(base='unknown', name='s2')),
          TypeRef(name='k3', type=Type(base='unknown', name='s3'), doc='d3')])))

  #----------------------------------------------------------------------------
  def test_parse_single_toplevel_anonymous_explicit(self):
    from .parser import parse
    self.assertEqual(
      parse('''\
        the prelude
        dict
          inner prelude
          k1 : s1
            d1
          k2 : s2
          k3 : s3
            d3
      '''),
      ('the prelude',
        Type(base='compound', name='dict', doc='inner prelude', value=[
          TypeRef(name='k1', type=Type(base='unknown', name='s1'), doc='d1'),
          TypeRef(name='k2', type=Type(base='unknown', name='s2')),
          TypeRef(name='k3', type=Type(base='unknown', name='s3'), doc='d3')])))

  #----------------------------------------------------------------------------
  def test_parse_single_toplevel_declarative(self):
    from .parser import parse
    self.assertEqual(
      parse('''\
        the prelude
        KeyMap
          inner prelude
          k1 : s1
            d1
          k2 : s2
          k3 : s3
            d3
      '''),
      ('the prelude',
        Type(base='dict', name='KeyMap', doc='inner prelude', value=[
          TypeRef(name='k1', type=Type(base='unknown', name='s1'), doc='d1'),
          TypeRef(name='k2', type=Type(base='unknown', name='s2')),
          TypeRef(name='k3', type=Type(base='unknown', name='s3'), doc='d3')])))

  #----------------------------------------------------------------------------
  def test_parse_single_namespaced_anonymous(self):
    from .parser import parse
    self.assertEqual(
      parse('''\
        the prelude
        keymap : dict
          inner prelude
          k1 : s1
            d1
          k2 : s2
          k3 : s3
            d3
      '''),
      ('the prelude',
        Type(base='compound', name='dict', value=[
          TypeRef(name='keymap', doc='inner prelude', type=
            Type(base='compound', name='dict', value=[
              TypeRef(name='k1', type=Type(base='unknown', name='s1'), doc='d1'),
              TypeRef(name='k2', type=Type(base='unknown', name='s2')),
              TypeRef(name='k3', type=Type(base='unknown', name='s3'), doc='d3')]))])))

  #----------------------------------------------------------------------------
  def test_parse_single_namespaced_declarative(self):
    from .parser import parse
    self.assertEqual(
      parse('''\
        the prelude
        keymap : KeyMap
          inner prelude
          k1 : s1
            d1
          k2 : s2
          k3 : s3
            d3
      '''),
      ('the prelude',
        Type(base='compound', name='dict', value=[
          TypeRef(name='keymap', type=
            Type(base='dict', name='KeyMap', doc='inner prelude', value=[
              TypeRef(name='k1', type=Type(base='unknown', name='s1'), doc='d1'),
              TypeRef(name='k2', type=Type(base='unknown', name='s2')),
              TypeRef(name='k3', type=Type(base='unknown', name='s3'), doc='d3')]))])))

  #----------------------------------------------------------------------------
  def test_parseMulti_custom_without_value_documents_attribute(self):
    from .parser import parseMulti
    self.assertEqual(
      list(parseMulti('''\
        prelude
        KeyMap
          keymap attr doc
        OtherMap
          OtherMap doc
          attr : type
      ''')),
      [
        ('prelude', Type(base='dict', name='KeyMap', doc='keymap attr doc')),
        (None, Type(base='dict', name='OtherMap', doc='OtherMap doc', value=[
          TypeRef(name='attr', type=Type(base='unknown', name='type')),
        ]))])

  #----------------------------------------------------------------------------
  def test_parseMulti_dual_namespaced_declarative(self):
    from .parser import parseMulti
    self.assertEqual(
      list(parseMulti('''\
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
      ''')),
      [
        ('the prelude',
          Type(base='compound', name='dict', doc='inner prelude a', value=[
            TypeRef(name='keymap', type=
              Type(base='dict', name='KeyMap', doc='inner prelude a.2', value=[
                TypeRef(name='k1', type=Type(base='unknown', name='s1'), doc='d1'),
                TypeRef(name='k2', type=Type(base='unknown', name='s2')),
                TypeRef(name='k3', type=Type(base='unknown', name='s3'), doc='d3')]))])),
        (None,
          Type(base='compound', name='dict', doc='inner prelude b', value=[
            TypeRef(name='othermap', type=
              Type(base='dict', name='OtherMap', doc='inner prelude b.2', value=[
                TypeRef(name='k1', type=Type(base='unknown', name='s1'))]))])),
      ])

  #----------------------------------------------------------------------------
  def test_parse_recursive(self):
    from .parser import parse
    self.assertEqual(
      parse('''\
        the prelude 1
        dict
          inner prelude 2
          keymap : KeyMap
            inner prelude 3
            k3 : S3
              inner prelude 4
              k4 : s4
      '''),
      ('the prelude 1',
        Type(base='compound', name='dict', doc='inner prelude 2', value=[
          TypeRef(name='keymap', type=
            Type(base='dict', name='KeyMap', doc='inner prelude 3', value=[
              TypeRef(name='k3', type=
                Type(base='dict', name='S3', doc='inner prelude 4', value=[
                  TypeRef(name='k4', type=Type(base='unknown', name='s4')),
                ]))]))])))

  #----------------------------------------------------------------------------
  def test_parse_rst_and_attributes(self):
    from .parser import parse
    self.assertEqual(
      parse('''\
        a preamble
        with a list:
          * one: 1
          * two
        k1 : v1
          d1
      '''),
      ('a preamble\nwith a list:\n    * one: 1\n    * two',
        Type(base='compound', name='dict', value=[
          TypeRef(name='k1', type=Type(base='unknown', name='v1'), doc='d1'),
        ])))

  #----------------------------------------------------------------------------
  def test_parse_rst_and_anonymous_dict(self):
    from .parser import parse
    self.assertEqual(
      parse('''\
        a preamble
        with a list:
          * one: 1
          * two
        dict
          inner prelude 2
          k1 : v1
      '''),
      ('a preamble\nwith a list:\n    * one: 1\n    * two',
        Type(base='compound', name='dict', doc='inner prelude 2', value=[
          TypeRef(name='k1', type=Type(base='unknown', name='v1')),
        ])))

#   # TODO: implement support for this...
#   # #----------------------------------------------------------------------------
#   # def test_parse_list_with_schema_and_no_attribute_comments(self):
#   #   from ...typereg import Type, TypeRef
#   #   from .plugin import parser
#   #   entry = aadict(doc=textwrap.dedent('''
#   #     Returns
#   #     -------
#   #     shape : list(Shape), default: null
#   #       Shape
#   #         A shape.
#   #         sides : int
#   #   '''))
#   #   self.assertEqual(
#   #     dict(parser(entry, self.context)),
#   #     dict(
#   #       doc='',
#   #       params=None,
#   #       returns=Type(base='compound', name='dict', value=[
#   #         TypeRef(name='shape', params=dict(default=None, optional=True),
#   #                 type=
#   #           Type(base='compound', name='list', value=
#   #             # note: this is a TypeRef *only* because the `resolveTypes`
#   #             #       call in `parser` converts Types to TypeRefs (so it
#   #             #       can be de-referenced later during merging.
#   #             TypeRef(type=
#   #               Type(base='dict', name='Shape', doc='A shape.', value=[
#   #                 TypeRef(name='sides', type=Type(base='scalar', name='integer'))
#   #               ]))))]),
#   #       raises=None,
#   #     ))

  #----------------------------------------------------------------------------
  def test_api_for_extensions(self):
    from ...typereg import Type, TypeRef
    from .parser import parseMulti
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
      list(parseMulti(src)),
      [
        ('this is doc1.',
          Type(base='dict', name='Type1', doc='type1 doc.', value=[
            TypeRef(name='foo', type=Type(base='scalar', name='integer')),
            TypeRef(name='bar', type=
              Type(base='dict', name='Shape', doc='a shape??', value=[
                TypeRef(name='sides', type=Type(base='scalar', name='integer')),
              ]))])),
        (None,
          TypeRef(name='shortstr', doc='short string must be short.', type=
            Type(base='scalar', name='string'), params={'max': 255}),
        ),
        (None,
          TypeRef(name='evenint', doc='even integral numbers only.', type=
            Type(base='scalar', name='integer'), params={'limit': 'even numbers only'}),
        ),
        ('doc2',
         Type(base='dict', name='Type2', doc='type-dos!', value=[
           TypeRef(name='three', type=Type(base='dict', name='Shape'), doc='a triangle.'),
         ])),
      ])

#------------------------------------------------------------------------------
# end of $Id$
# $ChangeLog$
#------------------------------------------------------------------------------
