# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2013/09/15
# copy: (C) Copyright 2013 Cadit Health Inc., All Rights Reserved.
#------------------------------------------------------------------------------

import re, six

#------------------------------------------------------------------------------
class PatternProxy(object):
  def __init__(self, expr, spec_args, spec_flags):
    self.__dict__['expr']       = expr
    self.__dict__['spec_args']  = spec_args
    self.__dict__['spec_flags'] = spec_flags
  def __setattr__(self, attr, value): return setattr(self.expr, attr, value)
  def __getattr__(self, attr): return getattr(self.expr, attr)
  def __delattr__(self, attr): return delattr(self.expr, attr)
  def __dir__(self): return dir(self.expr) + self.__dict__.keys()

#------------------------------------------------------------------------------
def reparse(spec, enhanced=False, accept_multiple=False):
  '''
  Parses `spec` as an encapsulated regular expression. The return
  value is compiled regular expression object (see `enhanced` for
  details).

  :Parameters:

  spec : str

    Encapsulated regular expression in the format "/EXPR/FLAGS", where
    "/" can be any character that does not exist elsewhere in the
    string and FLAGS is any of the one-character attributes defined in
    the system `re` python package. Any flags that do not exist in the
    `re` package are silently ignored.

  enhanced : bool, optional, default: false

    If false (the default), the returned object is the `re` package's
    compiled regular expression object. If true, it returns an enhanced
    proxy of the compile re object, with the following additional
    attributes:

    * `spec_flags`: the original FLAGS that were parsed.
    * `spec_args`: the tuple of parsed strings out of `spec`.
    * `expr`: the actual compiled regular expression being proxied.

    Note that `enhanced` is forced true if accept_multiple is true.

  accept_multiple: bool, optional, default: false

    Whether or not the `spec` should allow more than the two EXPR and
    FLAGS arguments, in which case the arguments are returned in the
    `spec_args` attribute. This is typically used when parsing a spec
    for the sed-style "s" command, e.g. "s/EXPR/REPL/FLAGS". If true,
    `enhanced` is forced true.
  '''
  if not isinstance(spec, six.string_types):
    return spec
  if not spec:
    raise ValueError('regex-spec must be in "/EXPR/FLAGS" format')
  if accept_multiple:
    enhanced = True
  sspec = spec.split(spec[0])
  if ( len(sspec) < 3 ) if accept_multiple else ( len(sspec) != 3 ):
    raise ValueError('regex-spec must be in "/EXPR/FLAGS" format')
  flags = 0
  for flag in sspec[-1].upper():
    flags |= getattr(re, flag, 0)
  expr = re.compile(sspec[1], flags)
  if not enhanced:
    return expr
  return PatternProxy(expr, sspec, sspec[-1])

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
