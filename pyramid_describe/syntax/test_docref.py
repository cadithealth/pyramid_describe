# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2014/05/06
# copy: (C) Copyright 2014-EOT Cadit Inc., All Rights Reserved.
#------------------------------------------------------------------------------

from pyramid_controllers.util import getVersion

from ..controller import DescribeController
from .. import test_helpers

#------------------------------------------------------------------------------
class TestDocref(test_helpers.TestHelper):

  #----------------------------------------------------------------------------
  def test_rst(self):
    from ..test.syntax_docref import Root
    root = Root()
    root.desc = DescribeController(
      root, doc='URL tree description.',
      settings={
        'formats'        : 'rst',
        'index-redirect' : 'false',
        'exclude'        : ('|^/desc(/.*)?$|'),
        'format.request' : 'true',
      })
    self.assertResponse(
      self.send(root, '/desc?showLegend=false&rstMax=true&showMeta=false'), 200,
      self.loadTestData('syntax_docref.output.rst'))

  #----------------------------------------------------------------------------
  def test_rstNoMax(self):
    from ..test.syntax_docref import Root
    root = Root()
    root.desc = DescribeController(
      root, doc='URL tree description.',
      settings={
        'formats'        : 'rst',
        'index-redirect' : 'false',
        'exclude'        : ('|^/desc(/.*)?$|'),
        'format.request' : 'true',
      })
    self.assertResponse(
      self.send(root, '/desc?showLegend=false&showMeta=false'), 200,
      self.loadTestData('syntax_docref-nomax.output.rst'))

  #----------------------------------------------------------------------------
  def test_html(self):
    from ..test.syntax_docref import Root
    root = Root()
    root.desc = DescribeController(
      root, doc='URL tree description.',
      settings={
        'formats'        : 'html',
        'index-redirect' : 'false',
        'exclude'        : ('|^/desc(/.*)?$|'),
        'format.request' : 'true',
      })
    self.assertResponse(
      self.send(root, '/desc?showLegend=false'), 200,
      self.loadTestData('syntax_docref.output.html', {
        'version' : getVersion('pyramid_describe'),
      }))

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
