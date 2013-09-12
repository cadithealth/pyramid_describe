# -*- coding: utf-8 -*-

from isstr import isstr

#------------------------------------------------------------------------------
def resolve(spec):
  if not isstr(spec):
    return spec
  if ':' in spec:
    spec, attr = spec.split(':', 1)
    return getattr(resolve(spec), attr)
  spec = spec.split('.')
  used = spec.pop(0)
  found = __import__(used)
  for cur in spec:
    used += '.' + cur
    try:
      found = getattr(found, cur)
    except AttributeError:
      __import__(used)
      found = getattr(found, cur)
  return found

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
