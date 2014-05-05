# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2013/09/09
# copy: (C) Copyright 2013 Cadit Health Inc., All Rights Reserved.
#------------------------------------------------------------------------------

import os, six
import re
from six.moves import urllib
from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.settings import asbool, aslist
from pyramid_controllers import Controller, index, ExposeDecorator, expose
from .describer import Describer
from .util import adict, pick, tobool

#------------------------------------------------------------------------------
class DescribeController(Controller):

  #----------------------------------------------------------------------------
  def __init__(self, view=None, settings=None, root=None, doc=None, *args, **kw):
    super(DescribeController, self).__init__(*args, **kw)
    if doc is not None:
      self.__doc__ = doc
    self.settings  = adict(settings or {})
    # todo: note that below there are several mentions of
    #       "settings.inspect" being improperly implemented... that is
    #       correct. the idea of `settings.inspect` is that it defines
    #       the path to begin traversal during reflection. instead, we
    #       are using a `settings.include` workaround. the problem
    #       with this workaround is performance...
    self.params    = adict(
      # todo: revert this when settings.inspect is properly implemented:
      #   view = view or self.settings.get('inspect') or '/',
      view = view or '/',
      # todo: revert this when settings.inspect is properly implemented:
      #   root = root or self.settings.get('inspect') or '/',
      root = root or '/',
    )
    # todo: enforce that `self.params.root` be a str...
    # todo: enforce that `self.params.inspect` be a str...
    # todo: remove this when settings.inspect is properly implemented:
    if self.settings.get('inspect') and self.settings.inspect != '/':
      path = self.settings.inspect
      if 'include' in self.settings:
        raise NotImplementedError()
      else:
        self.settings['include'] = []
      if path.endswith('/'):
        path = path[:-1]
      self.settings['include'].append(
        re.compile('^' + re.escape(path) + '(/.*)?$'))
    self.describer = Describer(settings=self.settings)
    # setup which extensions to handle
    self.fullname  = self.settings.get('fullname', 'application')
    self.handle_full = expose(
      name=self.fullname, ext=self.describer.formats)(self.handle_full)
    # setup the `basename` (i.e. the persistent location)
    self.basename  = self.settings.get('basename', None)
    if self.basename is not None:
      self.handle_base = expose(
        name=self.basename, ext=self.describer.formats)(self.handle_base)
    self.bredir = self.asredirect('base-redirect', 'true')
    self.iredir = self.asredirect('index-redirect', 'true')

  #----------------------------------------------------------------------------
  def asredirect(self, option, default):
    value = self.settings.get(option, default)
    try:
      code = int(value)
      return (code, None)
    except ValueError: pass
    try:
      if tobool(value, force=False):
        return (HTTPFound.code, None)
      return False
    except ValueError: pass
    value = aslist(value)
    if len(value) < 0 or len(value) > 2:
      raise ValueError('invalid %s list value: %r' % (option, value))
    if len(value) == 1:
      return (HTTPFound.code, value[0])
    try:
      return (int(value[0]), value[1])
    except ValueError:
      raise ValueError('invalid %s response code: %r' % (option, value[0]))

  #----------------------------------------------------------------------------
  def describe(self, request, format):
    context = adict(request=request)
    def get_options(fmt):
      rset = None
      if fmt is not None:
        rset = self.settings.get('format.' + fmt + '.request', None)
      if rset is None:
        rset = self.settings.get('format.request', None)
      if rset is None:
        return dict()
      try:
        if tobool(rset, force=False):
          return request.params
      except ValueError: pass
      return pick(request.params, *aslist(rset))
    if format is None:
      format = get_options(None).get('format', None)
    context.get_options = get_options
    res = self.describer.describe(
      self.params.view, context, format=format, root=self.params.root)
    if res.content_type:
      request.response.content_type = res.content_type
    if res.charset:
      request.response.charset = res.charset
    return res.content

  #----------------------------------------------------------------------------
  @index(forceSlash=False)
  def handle_index(self, request):
    if not self.iredir or not asbool(request.params.get('redirect', 'true')):
      return self.describe(request, None)
    ext = self.describer.defformat
    url = request.path_url
    if not url.endswith('/'):
      url += '/'
    url = urllib.parse.urljoin(
      url, self.iredir[1] or ( ( self.basename or self.fullname ) + '.' + ext ) )
    if not self.iredir[1] and request.query_string:
      url += '?' + request.query_string
    request.response.status_code = self.iredir[0]
    request.response.headers['Location'] = url
    return request.response

  #----------------------------------------------------------------------------
  # NOTE: this method is exposed dynamically at run-time in __init__
  def handle_full(self, request):
    path, ext = os.path.splitext(request.path)
    if ext and ext.startswith('.'):
      ext = ext[1:]
    return self.describe(request, ext)

  #----------------------------------------------------------------------------
  # NOTE: this method is OPTIONALLY exposed dynamically at run-time in __init__
  def handle_base(self, request):
    ext = os.path.splitext(request.path)[1]
    if ext.startswith('.'):
      ext = ext[1:]
    if not self.bredir or not asbool(request.params.get('redirect', 'true')):
      return self.describe(request, ext)
    url = urllib.parse.urljoin(
      request.path_url, self.bredir[1] or ( self.fullname + '.' + ext ) )
    if not self.bredir[1] and request.query_string:
      url += '?' + request.query_string
    request.response.status_code = self.bredir[0]
    request.response.headers['Location'] = url
    return request.response

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
