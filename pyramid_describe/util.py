# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2013/09/09
# copy: (C) Copyright 2013 Cadit Health Inc., All Rights Reserved.
#------------------------------------------------------------------------------

from pyramid.settings import aslist
from pyramid_controllers.util import adict, pick

from .isstr import isstr
from .resolve import resolve
from .reparse import reparse

#------------------------------------------------------------------------------
def runFilters(filters, target, *args, **kw):
  if not target:
    return None
  if not filters:
    return target
  for filt in filters:
    target = filt(target, *args, **kw)
    if not target:
      break
  return target

#------------------------------------------------------------------------------
def tolist(obj):
  if not obj:
    return []
  if isstr(obj):
    return aslist(obj)
  if isinstance(obj, (list, tuple)):
    return obj
  return [obj]

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
