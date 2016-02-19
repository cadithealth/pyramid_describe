# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2016/01/11
# copy: (C) Copyright 2016-EOT Cadit Inc., All Rights Reserved.
#------------------------------------------------------------------------------

import unittest

#------------------------------------------------------------------------------
class TestParams(unittest.TestCase):

  #----------------------------------------------------------------------------
  def test_qualifier_ordering(self):
    from .params import attrkeycmp
    keys = ['foo', 'default', 'required', 'min', 'example', 'max', 'default_to', 'examples']
    chk  = ['required', 'foo', 'max', 'min', 'example', 'examples', 'default_to', 'default']
    self.assertEqual(sorted(keys, cmp=attrkeycmp), chk)

  #----------------------------------------------------------------------------
  def test_parse_simple(self):
    from .params import parse
    self.assertEqual(
      parse('not-empty, @PUBLIC, default: "zoo"'),
      {'not_empty': True, 'optional': True, '@PUBLIC': True, 'default': 'zoo'})

  #----------------------------------------------------------------------------
  def test_parse_collision(self):
    from .params import parse
    self.assertEqual(
      parse('not-empty, not-empty: true'),
      {'not_empty': True})
    with self.assertRaises(ValueError) as cm:
      parse('not-empty, not-empty: false')
    self.assertEqual(
      str(cm.exception),
      'qualifier "not-empty" collision (True != False)')
    with self.assertRaises(ValueError) as cm:
      parse('example: foo, examples: "bar"')
    self.assertEqual(
      str(cm.exception),
      'both "example" and "examples" qualifiers specified')
    with self.assertRaises(ValueError) as cm:
      parse('default-to: foo, default: "bar"')
    self.assertEqual(
      str(cm.exception),
      'both "default" and "default-to" qualifiers specified')

  #----------------------------------------------------------------------------
  def test_parse_example_multiple(self):
    from .params import parse
    self.assertEqual(
      parse('example: foo, example: bar'),
      {'example': ['foo', 'bar']})

  #----------------------------------------------------------------------------
  def test_parse_examples(self):
    from .params import parse
    self.assertEqual(
      parse('examples: "foo"'),
      {'examples': ['foo']})
    self.assertEqual(
      parse('examples: "foo" | 6 | \'bar\''),
      {'examples': ['foo', 6, 'bar']})

  #----------------------------------------------------------------------------
  def test_parse_example_autoconvert(self):
    from .params import parse
    self.assertEqual(
      parse('example: "foo", example: "bar", example: 6'),
      {'examples': ['foo', 'bar', 6]})
    self.assertEqual(
      parse('example: foo, example: "bar", example: 6'),
      {'example': ['foo', 'bar', 6]})
    # todo: re-enable this when the side-effect of changing order is removed...
    # self.assertEqual(
    #   parse('example: "foo", example: bar, example: 6'),
    #   {'example': ['foo', 'bar', 6]})

  #----------------------------------------------------------------------------
  def test_parse_default_json(self):
    from .params import parse
    self.assertEqual(parse('default: 6'),     {'default': 6,     'optional': True})
    self.assertEqual(parse('default: true'),  {'default': True,  'optional': True})
    self.assertEqual(parse('default: "foo"'), {'default': 'foo', 'optional': True})

  #----------------------------------------------------------------------------
  def test_parse_default_fallback(self):
    from .params import parse
    self.assertEqual(parse("default: foo"),   {'default_to': 'foo', 'optional': True})

  #----------------------------------------------------------------------------
  def test_parse_default_yaml(self):
    from .params import parse
    self.assertEqual(parse("default: 'foo'"), {'default': 'foo', 'optional': True})

  #----------------------------------------------------------------------------
  def test_value_codec(self):
    from .params import render, parse
    src = {
      's1' : 'a string',
      's2' : '6',
      'i1' : 6,
    }
    self.assertEqual(render(src), 'i1: 6, s1: a string, s2: "6"')
    self.assertEqual(parse(render(src)), src)

  # TODO: add access parameter unit tests...


#------------------------------------------------------------------------------
# end of $Id$
# $ChangeLog$
#------------------------------------------------------------------------------
