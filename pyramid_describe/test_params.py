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
