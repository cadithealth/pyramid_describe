# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2014/05/07
# copy: (C) Copyright 2014-EOT Cadit Inc., All Rights Reserved.
#------------------------------------------------------------------------------

import pkg_resources
import pyramid_controllers.test_helpers

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
# end of $Id$
#------------------------------------------------------------------------------
