# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2016/02/19
# copy: (C) Copyright 2016-EOT Cadit Inc., All Rights Reserved.
#------------------------------------------------------------------------------

import unittest

from . import constant

#------------------------------------------------------------------------------
class TestConstant(unittest.TestCase):

  #----------------------------------------------------------------------------
  def test_parse_invalid(self):
    for val, exc in [
        ('',            "invalid constant: ''"),
        ('0x',          "invalid constant (tried hex): '0x'"),
        ('-x',          "No JSON object could be decoded"),
        ('- 1',         "No JSON object could be decoded"),
        ('no',          "No JSON object could be decoded"),
        ('"no',         "invalid constant (tried yaml): '\"no'"),
      ]:
      with self.assertRaises(ValueError) as cm:
        constant.parse(val)
      self.assertEqual(str(cm.exception), exc)

  #----------------------------------------------------------------------------
  def test_hex(self):
    self.assertEqual(constant.parse('0x61'),     'a')
    self.assertEqual(constant.parse('0x616263'), 'abc')

  #----------------------------------------------------------------------------
  def test_bool(self):
    self.assertEqual(constant.parse('true'),  True)
    self.assertEqual(constant.parse('false'), False)

  #----------------------------------------------------------------------------
  def test_null(self):
    self.assertEqual(constant.parse('null'),  None)
    self.assertEqual(constant.parse(' null '),  None)

  #----------------------------------------------------------------------------
  def test_num(self):
    self.assertEqual(constant.parse('61'),   61)
    self.assertEqual(constant.parse('87.8'), 87.8)
    self.assertEqual(constant.parse('-87.8'), -87.8)

  #----------------------------------------------------------------------------
  def test_str(self):
    self.assertEqual(constant.parse('"foo"'),    'foo')
    self.assertEqual(constant.parse("'foo'"),    'foo')
    self.assertEqual(constant.parse('0x666f6f'), 'foo')

  #----------------------------------------------------------------------------
  def test_list(self):
    self.assertEqual(constant.parse('["foo", \'bar\', 6]'), ['foo', 'bar', 6])

  #----------------------------------------------------------------------------
  def test_dict(self):
    self.assertEqual(constant.parse('{a: 10, "b": foo}'), dict(a=10, b='foo'))

  #----------------------------------------------------------------------------
  def test_multi(self):
    self.assertEqual(constant.parseMulti('"foo"', '|'), ['foo'])
    self.assertEqual(constant.parseMulti('"foo" |6|0x61 ', '|'), ['foo', 6, 'a'])
    self.assertEqual(constant.parseMulti(' null | 6|0x61 ', '|'), [None, 6, 'a'])


#------------------------------------------------------------------------------
# end of $Id$
# $ChangeLog$
#------------------------------------------------------------------------------
