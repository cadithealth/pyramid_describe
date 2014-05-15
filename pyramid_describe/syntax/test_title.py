# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2014/05/06
# copy: (C) Copyright 2014-EOT Cadit Inc., All Rights Reserved.
#------------------------------------------------------------------------------

from ..util import adict
from .. import test_helpers
from . import title

#------------------------------------------------------------------------------
class TestTitle(test_helpers.TestHelper):

  #----------------------------------------------------------------------------
  def test_names(self):
    ## ensure a bare minimum of section names are loaded
    minimum = set(['Parameters', 'Returns', 'Raises'])
    self.assertTrue(minimum <= title.getNames())

  #----------------------------------------------------------------------------
  def test_start(self):
    src = '''\
:Parameters:

Dict of supported parameters.
'''
    chk = '''\
Parameters
----------

Dict of supported parameters.'''
    out = title.parser(adict(doc=src), adict()).doc
    self.assertMultiLineEqual(out, chk)

  #----------------------------------------------------------------------------
  def test_middle(self):
    src = '''\
Some label.

:Parameters:

Dict of supported parameters.

:Returns:

List of returnable items.
'''
    chk = '''\
Some label.

Parameters
----------

Dict of supported parameters.

Returns
-------

List of returnable items.'''
    out = title.parser(adict(doc=src), adict()).doc
    self.assertMultiLineEqual(out, chk)

  #----------------------------------------------------------------------------
  def test_end(self):
    src = '''\
A description.

:Returns:
'''
    chk = '''\
A description.

Returns
-------'''
    out = title.parser(adict(doc=src), adict()).doc
    self.assertMultiLineEqual(out, chk)

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
