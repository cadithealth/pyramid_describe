# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2014/05/06
# copy: (C) Copyright 2014-EOT Cadit Inc., All Rights Reserved.
#------------------------------------------------------------------------------

from ..controller import DescribeController
from .. import test_helpers

#------------------------------------------------------------------------------
class TestNumpydoc(test_helpers.TestHelper):

  #----------------------------------------------------------------------------
  def test_rst(self):
    from ..test.syntax_numpydoc import Root
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
    self.assertResponse(
      self.send(root, '/desc?showLegend=false&rstMax=true&showMeta=false'), 200,
      self.loadTestData('syntax_numpydoc.output.rst'))

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
