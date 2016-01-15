# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2015/12/01
# copy: (C) Copyright 2015-EOT Cadit Inc., All Rights Reserved.
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
class Scope(object):
  '''
  A `Scope` object is an aadict-style key/value container, where the
  values can be inherited from a "parent" Scope instance. Note that
  although a Scope can be modified, its "parent" is never modified.
  '''

  #----------------------------------------------------------------------------
  def __init__(self, *args, **kw):
    self.__dict__['parent']  = None
    self.__dict__['values']  = dict()
    self.__dict__['deletes'] = []
    if len(args) > 0:
      self.__dict__['parent'] = args[0]
      args = args[1:]
    self.update(*args, **kw)

  # todo: perhaps also add the following methods:
  #         __iter__
  #         __len__
  #         __missing__
  #         __cmp__
  #         __eq__
  #         __ne__
  #         __lt__
  #         __gt__
  #         __le__
  #         __ge__

  #----------------------------------------------------------------------------
  def __contains__(self, key):
    if key in self.__dict__['deletes']:
      return False
    if key in self.__dict__['values']:
      return True
    if self.__dict__['parent']:
      return key in self.__dict__['parent']
    return False

  #----------------------------------------------------------------------------
  def __getattr__(self, key):
    if key in self.__dict__['deletes']:
      return None
    if key in self.__dict__['values']:
      return self.__dict__['values'][key]
    if self.__dict__['parent']:
      return getattr(self.__dict__['parent'], key)
    return None

  #----------------------------------------------------------------------------
  def __setattr__(self, key, value):
    if key in self.__dict__['deletes']:
      self.__dict__['deletes'].remove(key)
    self.__dict__['values'][key] = value
    return self

  #----------------------------------------------------------------------------
  def __delattr__(self, key):
    if key in self.__dict__['deletes']:
      return self
    if key in self.__dict__['values']:
      self.__dict__['values'].pop(key)
    if self.__dict__['parent'] and key in self.__dict__['parent']:
      self.__dict__['deletes'].append(key)
    return self

  #----------------------------------------------------------------------------
  def __getitem__(self, key):         return self.__getattr__(key)
  def __setitem__(self, key, value):  return self.__setattr__(key, value)
  def __delitem__(self, key):         return self.__delattr__(key)

  #----------------------------------------------------------------------------
  def keys(self):
    if self.__dict__['parent']:
      for key in self.__dict__['parent'].keys():
        if key in self:
          yield key
    for key in self.__dict__['values']:
      if key in (self.__dict__['parent'] or []):
        continue
      yield key

  #----------------------------------------------------------------------------
  def items(self):
    for key in self.keys():
      yield (key, getattr(self, key))

  #----------------------------------------------------------------------------
  def values(self):
    for key in self.keys():
      yield getattr(self, key)

  #----------------------------------------------------------------------------
  def update(self, *args, **kw):
    for arg in list(args) + [kw]:
      for key, val in arg.items() if arg else []:
        setattr(self, key, val)
    return self

  #----------------------------------------------------------------------------
  def spawn(self, *args, **kw):
    return Scope(self).update(*args, **kw)


#------------------------------------------------------------------------------
# end of $Id$
# $ChangeLog$
#------------------------------------------------------------------------------
