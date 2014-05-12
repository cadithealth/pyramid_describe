# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2014/05/07
# copy: (C) Copyright 2014-EOT Cadit Inc., All Rights Reserved.
#------------------------------------------------------------------------------

from . import docref
from . import title
from . import numpydoc
from . import docorator

#------------------------------------------------------------------------------
def parser(entry, options):
  for subparser in (docref.parser, title.parser, numpydoc.parser, docorator.parser):
    if not entry:
      break
    entry = subparser(entry, options)
  return entry

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
