# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2013/09/09
# copy: (C) Copyright 2013 Cadit Health Inc., All Rights Reserved.
#------------------------------------------------------------------------------

import re
import json
import binascii

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
def jsonParse(text, partial=False):
  '''
  JSON-decodes `text` and returns the result. If `partial` is truthy,
  then JSON-decodes as much of `text` as possible (at least *some*),
  and returns a tuple of (result, remainder-text).
  '''
  if not partial:
    return json.loads(text)
  try:
    return ( json.loads(text), '' )
  except ValueError as exc:
    if not str(exc).startswith('Extra data: line 1 column '):
      raise
    # NOTE: first trying idx as-is, then idx-1 because json changed
    #       from being 0-based to 1-based from python 2.7.3 to 2.7.6.
    idx = int(str(exc).split()[5])
    try:
      return ( json.loads(text[:idx]), text[idx:] )
    except ValueError as exc:
      if not str(exc).startswith('Extra data: line 1 column '):
        raise
    idx = idx - 1
    return ( json.loads(text[:idx]), text[idx:] )

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
