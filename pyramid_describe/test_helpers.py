# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2014/05/07
# copy: (C) Copyright 2014-EOT Cadit Inc., All Rights Reserved.
#------------------------------------------------------------------------------

import unittest

import pkg_resources
import pyramid_controllers.test_helpers
import asset

#------------------------------------------------------------------------------
class TestHelper(pyramid_controllers.test_helpers.TestHelper):

  maxDiff = None

  #----------------------------------------------------------------------------
  def loadTestData(self, name, symbols=None):
    data = pkg_resources.resource_string('pyramid_describe', 'test/' + name)
    if symbols:
      # todo: convert to mustache?...
      for key, val in symbols.items():
        data = data.replace('{{' + key + '}}', val)
    return data


#------------------------------------------------------------------------------
def plugin_test_symbol(): pass
plugin_test_symbol.after = 'numpydoc'
plugin_test_symbol.before = 'docorator'

#------------------------------------------------------------------------------
class TestPlugins(unittest.TestCase):

  #----------------------------------------------------------------------------
  def test_parsers_standard(self):
    self.assertEqual(
      [p.name for p in asset.plugins('pyramid_describe.plugins.entries.parsers')],
      ['docref', 'title', 'numpydoc', 'docorator'])

  #----------------------------------------------------------------------------
  def test_parsers_extra_asset(self):
    self.assertEqual(
      [p.name for p in asset.plugins(
        'pyramid_describe.plugins.entries.parsers',
        '+pyramid_describe.test_helpers.plugin_test_symbol',
      )],
      ['docref', 'title', 'numpydoc',
       'pyramid_describe.test_helpers.plugin_test_symbol',
       'docorator'])


#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
