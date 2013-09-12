# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2013/09/10
# copy: (C) Copyright 2013 Cadit Health Inc., All Rights Reserved.
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
class adict(dict):
  def __getattr__(self, key):
    if key.startswith('__') and key.endswith('__'):
      # note: allows an adict to be pickled with protocols 0, 1, and 2
      #       which treat the following specially:
      #         __getstate__, __setstate__, __slots__, __getnewargs__
      return dict.__getattr__(self, key)
    return self.get(key, None)
  def __setattr__(self, key, value):
    self[key] = value
    return self
  def __delattr__(self, key):
    if key in self:
      del self[key]
    return self
  def update(self, *args, **kw):
    args = [e for e in args if e]
    dict.update(self, *args, **kw)
    return self
  def pick(self, *args):
    return adict({k: v for k, v in self.iteritems() if k in args})
  def omit(self, *args):
    return adict({k: v for k, v in self.iteritems() if k not in args})
  @staticmethod
  def __dict2adict__(subject, recursive=False):
    if isinstance(subject, list):
      if not recursive:
        return subject
      return [adict.__dict2adict__(val, True) for val in subject]
    if not isinstance(subject, dict):
      return subject
    ret = adict(subject)
    if not recursive:
      return ret
    for key, val in ret.items():
      ret[key] = adict.__dict2adict__(val, True)
    return ret

#------------------------------------------------------------------------------
def pick(source, *keys):
  '''
  Given a dict and iterable of keys, return a dict containing only
  those keys.
  '''
  if not source: # pragma: no cover
    return dict()
  try:
    return {k: v for k, v in source.items() if k in keys}
  except AttributeError:
    return {k: getattr(source, k) for k in keys if hasattr(source, k)}

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
