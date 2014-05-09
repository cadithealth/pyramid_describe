# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2013/09/09
# copy: (C) Copyright 2013 Cadit Health Inc., All Rights Reserved.
#------------------------------------------------------------------------------

import re, binascii
from pyramid.settings import aslist, asbool, truthy
from pyramid_controllers.util import adict, pick

from .isstr import isstr
from .resolve import resolve
from .reparse import reparse

falsy = frozenset(('f', 'false', 'n', 'no', 'off', '0'))
booly = frozenset(list(truthy) + list(falsy)) 

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
def tobool(val, force=True):
  if force or val.lower() in booly:
    return asbool(val)
  raise ValueError('invalid literal for tobool(): %r', (val,))

#------------------------------------------------------------------------------
def tolist(obj):
  if not obj:
    return []
  if isstr(obj):
    try:
      return aslist(obj)
    except TypeError:
      pass
  if isinstance(obj, (list, tuple)):
    return obj
  try:
    return [e for e in obj]
  except TypeError:
    pass
  return [obj]

#------------------------------------------------------------------------------
def tag(text):
  return binascii.hexlify(text).lower()

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
