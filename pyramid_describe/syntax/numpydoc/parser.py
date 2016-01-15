# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2015/12/28
# copy: (C) Copyright 2015-EOT Cadit Inc., All Rights Reserved.
#------------------------------------------------------------------------------

import logging
import json

from ...typereg import TypeRef
from ...params import parse as parseParams

#------------------------------------------------------------------------------

log = logging.getLogger(__name__)

#------------------------------------------------------------------------------
def parseSpec(context, spec):
  # TODO: move typespec parsing from typereg to here...
  typ, par = context.options.typereg.parseType(spec, complete=False)
  if par:
    par = par.strip()
    if not par.startswith(','):
      raise ValueError('invalid type specification: %r' % (spec,))
    par = parseParams(par[1:])
  return (typ, par or None)

#------------------------------------------------------------------------------
# end of $Id$
# $ChangeLog$
#------------------------------------------------------------------------------
