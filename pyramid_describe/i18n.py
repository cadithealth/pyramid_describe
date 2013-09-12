# -*- coding: utf-8 -*-

from gettext import gettext

#------------------------------------------------------------------------------
def _(message, *args, **kw):
  if args or kw:
    return gettext(message).format(*args, **kw)
  return gettext(message)

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
