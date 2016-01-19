# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2016/01/17
# copy: (C) Copyright 2016-EOT Cadit Inc., All Rights Reserved.
#------------------------------------------------------------------------------

import unittest
import textwrap

#------------------------------------------------------------------------------
class TestExtractor(unittest.TestCase):

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

  # TODO: enable this when implemented...
  # #----------------------------------------------------------------------------
  # def test_FixedNumpyDocString_consistent_empty_lines(self):
  #   from .extractor import FixedNumpyDocString
  #   src = textwrap.dedent('''\
  #     Returns
  #     -------
  #     Returns a shape, as follows:
  #
  #     Shape
  #
  #         A regular two-dimensional filled polygon.
  #
  #         sides : int
  #
  #             The number of sides of the shape.
  #
  #             .. code:: text
  #
  #                 Some text.
  #
  #
  #                 Two lines above
  #                 and one line below.
  #
  #                 The end.''')
  #   self.assertMultiLineEqual(str(FixedNumpyDocString(src)), src)


#------------------------------------------------------------------------------
# end of $Id$
# $ChangeLog$
#------------------------------------------------------------------------------
