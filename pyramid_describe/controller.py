# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2013/09/09
# copy: (C) Copyright 2013 Cadit Health Inc., All Rights Reserved.
#------------------------------------------------------------------------------

import os
from pyramid_controllers import Controller, index, ExposeDecorator, expose
from .describer import Describer
from .util import adict

#------------------------------------------------------------------------------
class DescribeController(Controller):

  #----------------------------------------------------------------------------
  def __init__(self, view=None, settings=None, root=None, doc=None, *args, **kw):
    super(DescribeController, self).__init__(*args, **kw)
    if doc is not None:
      self.__doc__ = doc
    self.describer = Describer(settings=settings)
    self.settings  = adict(settings or {})
    self.params    = adict(view=view, root=root or '/')
    self.handle    = expose(
      name = self.settings.get('name', 'application'),
      ext  = self.describer.formats,
      )(self.handle)

  #----------------------------------------------------------------------------
  def describe(self, request, format):
    return self.describer.describe(
      self.params.view, request, format=format, root=self.params.root)

  #----------------------------------------------------------------------------
  @index(forceSlash=False)
  def index(self, request):
    return self.describe(request, None)

  #----------------------------------------------------------------------------
  # NOTE: this method is exposed dynamically at run-time in __init__
  def handle(self, request):
    path, ext = os.path.splitext(request.path)
    if ext and ext.startswith('.'):
      ext = ext[1:]
    return self.describe(request, ext)

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
