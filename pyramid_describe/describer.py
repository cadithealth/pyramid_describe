# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2013/09/10
# copy: (C) Copyright 2013 Cadit Health Inc., All Rights Reserved.
#------------------------------------------------------------------------------

import re
import logging
import inspect
import binascii
import types
import json

import six
import yaml
from six.moves import urllib
from docutils.core import publish_from_doctree
from pyramid.interfaces import IMultiView
from pyramid.settings import asbool, truthy
from pyramid.renderers import render as pyramid_render
from pyramid_controllers import Controller, RestController, Dispatcher
from pyramid_controllers.restcontroller import meth2action, action2meth, HTTP_METHODS
from pyramid_controllers.dispatcher import getDispatcherFromStack
import asset
from aadict import aadict
import morph

from .entry import Entry
from .scope import Scope
from .typereg import TypeRegistry
from .util import adict, isstr, tolist, resolve, pick, reparse, runFilters, tag
from . import rst, doctree, render
from .i18n import _

#------------------------------------------------------------------------------

log = logging.getLogger(__name__)

DEFAULT   = 'pyramid_describe:DEFAULT'
FORMATS   = ('html', 'txt', 'rst', 'json', 'wadl', 'yaml', 'xml')

DEFAULT_METHODS_ORDER = ('post', 'get', 'put', 'delete')

try:
  import pdfkit
  FORMATS += ('pdf',)
except ImportError:
  pdfkit = None

#------------------------------------------------------------------------------
class DescriberCatalog(adict):
  @property
  def tree_entries(self):
    # todo: make this a bit more "rigorous"...
    '''
    Generates a "complete" set of entries that includes all branch
    entries. These branch entries, however, should not have their
    documentation shown. Also sorts the entries by name unless RESTful
    - this is so that RESTful methods show up first (since they
    technically don't exist in the URL path). The following Entry
    attributes are added:
      * _dreal
      * _dlast
      * _dchildren
    '''
    fullset = []
    for entry in self.endpoints:
      entry._dreal = True
      if entry.parent and entry.parent not in fullset:
        toadd = []
        for parent in entry.parents:
          if parent not in fullset:
            toadd.append(parent)
            continue
          break
        fullset.extend(reversed(toadd))
      fullset.append(entry)
      if entry.isRest and entry.isController and entry.methods:
        for method in entry.methods:
          method._dreal = True
          fullset.append(method)
    entries = fullset
    # decorate entries with '_dlast' attribute...
    for entry in entries:
      if entry.parent:
        if entry.parent._dchildren is None:
          entry.parent._dchildren = []
        entry.parent._dchildren.append(entry)
    for entry in entries:
      if entry._dchildren:
        entry._dchildren[-1]._dlast = True
    return entries

#------------------------------------------------------------------------------
def extract(settings, prefix):
  if not settings:
    return adict()
  prefix += '.'
  return adict({name[len(prefix):] : value
                for name, value in settings.items()
                if name.startswith(prefix)})

#------------------------------------------------------------------------------
def tocallables(spec, attr):
  if not spec:
    return None
  ret = [resolve(e) for e in tolist(spec)]
  return [
    e if six.callable(e) else getattr(e, attr)
    for e in ret]

#------------------------------------------------------------------------------
def methOrderKey(methods):
  methods = [m.lower() for m in methods]
  def _sort(method):
    method = method.name.lower()
    try:
      return (0, methods.index(method))
    except ValueError:
      return (1, method)
  return _sort

#------------------------------------------------------------------------------
class Describer(object):

  legend = (
    ('STUB',
     _('Placeholder -- usually replaced with an ID or other'
       ' identifier of a RESTful object.')),
    ('REST',
     _('Not an actual endpoint, but the HTTP method to use.')),
    ('DYNAMIC',
     _('Dynamically evaluated endpoint; no further information can be'
       ' determined without request-specific details.')),
    (Dispatcher.NAME_DEFAULT,
     _('This endpoint is a `default` handler, and is therefore free to interpret'
       ' path arguments dynamically; no further information can be determined'
       ' without request-specific details.')),
    (Dispatcher.NAME_LOOKUP,
     _('This endpoint is a `lookup` handler, and is therefore free to interpret'
       ' path arguments dynamically; no further information can be determined'
       ' without request-specific details.')),
  )

  content_types = {
    'html'  : ('text/html',          'UTF-8'),
    'json'  : ('application/json',   'UTF-8'),
    'pdf'   : ('application/pdf',    'UTF-8'),
    'rst'   : ('text/x-rst',         'UTF-8'),
    'txt'   : ('text/plain',         'UTF-8'),
    'wadl'  : ('text/xml',           'UTF-8'),
    'xml'   : ('text/xml',           'UTF-8'),
    'yaml'  : ('application/yaml',   'UTF-8'),
  }

  bool_options = (
    ('showUnderscore', False),
    ('showUndoc',      True),
    ('showLegend',     True),
    ('showBranches',   False),
    ('pruneIndex',     True),
    ('showRest',       True),
    ('showImpl',       False),
    ('showInfo',       True),
    ('showMeta',       True),
    ('showName',       True),
    ('showDecorated',  True),
    ('showExtra',      True),
    ('showMethods',    True),
    ('showIds',        True),
    ('showDynamic',    True),
    ('showGenerator',  True),
    ('showGenVersion', True),
    ('showLocation',   True),
    ('ascii',          False),
    ('rstMax',         False),
    ('rstPdfkit',      True),
    ('cssEmbed',       True),
  )

  int_options = (
    ('maxdepth',       1024),
    ('width',          79),
    ('maxDocColumn',   None),
    ('minDocLength',   20),
  )

  list_options = (
    ('restVerbs',      HTTP_METHODS),
    ('filters',        None),
  )

  str_options = (
    ('catalog.parsers',  '*'),
    ('catalog.filters',  '*'),
    ('entry.parsers',    '*'),
    ('entry.filters',    '*'),
    ('commentToken',     '##'),
    ('title',            None),
    ('endpoints.title',  None),
    ('legend.title',     None),
    ('stubFormat',       '{{{}}}'),     # /path/to/{NAME}/and/more
    ('dynamicFormat',    '{}/?'),       # /path/to/NAME/?
    ('restFormat',       '<{}>'),       # /path/to/<NAME>
    ('cssPath',          'pyramid_describe:template/rst2html.css'),
    ('encoding',         'UTF-8'),
    ('rstWriter',        'pyramid_describe.writers.rst.Writer'),

    ('typereg.title',    'Types'),
    ('typereg.noDef',    'N/A'),
    ('typereg.aliases',  None),
    ('type.parsers',     '*'),
    ('type.filters',     '*'),

    ('access.control',            None),
    ('access.default.endpoint',   None),
    ('access.default.type',       None),
    ('access.default.attribute',  'public'),
    ('access.rank',               'public beta internal'),
    ('access.group.public',       '@PUBLIC'),
    ('access.group.beta',         '@BETA'),
    ('access.group.internal',     '@INTERNAL'),

    ('pdfkit.options',   '''\
{
  margin-top: 10mm,
  margin-right: 10mm,
  margin-bottom: 10mm,
  margin-left: 10mm,
}
'''),
  )

  # TODO: support per-format system defaults...
  # todo: then, change cssPath to be html-only.

  #----------------------------------------------------------------------------
  def __init__(self, settings=None, default=None, override=None):
    self.settings  = adict(settings or dict())
    self.include   = [reparse(expr) if isstr(expr) else expr
                      for expr in tolist(self.settings.include or '')]
    self.exclude   = [reparse(expr) if isstr(expr) else expr
                      for expr in tolist(self.settings.exclude or '')]
    self.formats   = tolist(self.settings.formats or '') or FORMATS
    self.defformat = self.settings.get('format.default', self.formats[0])
    # load the renderer, default and override options
    self.renderers = dict()
    self.options   = dict()
    self.override  = dict()
    self.options[None] = extract(self.settings, 'format.default')
    self.options[None].update(default or dict())
    self.override[None] = extract(self.settings, 'format.override')
    self.override[None].update(override or dict())
    # note that all format settings must be extracted since there may
    # be cascaded formatting calls (instead of just restricting it to
    # the set in `self.formats`...
    fmts = set([k.split('.', 2)[1] for k in self.settings.keys()
                if k.startswith('format.') and '.' in k[8:]])
    fmts -= set(['default', 'override'])
    for fmt in fmts:
      rndr = self.settings.get('format.' + fmt + '.renderer', None)
      if rndr:
        self.renderers[fmt] = rndr
      self.options[fmt]  = extract(self.settings, 'format.' + fmt + '.default')
      self.override[fmt] = extract(self.settings, 'format.' + fmt + '.override')
    # load the entry/type/catalog parsers and filters
    stropts = dict(self.str_options)
    self.eparsers = asset.plugins(
      'pyramid_describe.plugins.entry.parsers',
      self.settings.get('entry.parsers', stropts.get('entry.parsers')))
    self.tparsers = asset.plugins(
      'pyramid_describe.plugins.type.parsers',
      self.settings.get('type.parsers', stropts.get('type.parsers')))
    self.cparsers = asset.plugins(
      'pyramid_describe.plugins.catalog.parsers',
      self.settings.get('catalog.parsers', stropts.get('catalog.parsers')))
    self.efilters = asset.plugins(
      'pyramid_describe.plugins.entry.filters',
      self.settings.get('entry.filters', stropts.get('entry.filters')))
    self.tfilters = asset.plugins(
      'pyramid_describe.plugins.type.filters',
      self.settings.get('type.filters', stropts.get('type.filters')))
    self.cfilters = asset.plugins(
      'pyramid_describe.plugins.catalog.filters',
      self.settings.get('catalog.filters', stropts.get('catalog.filters')))
    self.render_template = self.settings.get('render.template', None)
    self.methOrderKey = methOrderKey(
      tolist(self.settings.get('methods.order', DEFAULT_METHODS_ORDER)))
    tropts = morph.pick(self.settings, prefix='typereg.')
    tropts['commentToken'] = self.settings.get(
      'commentToken', dict(self.str_options).get('commentToken'))
    self.typereg = TypeRegistry(tropts)

  #----------------------------------------------------------------------------
  def describe(self, view, context=None, format=None, root=None):
    context = adict(context or {})
    if context.request is None:
      # this is really not the "right thing", but it makes a lot of other
      # coding quicker...
      context.request = adict()
    if format is None:
      format = self.defformat
    options = self._getOptions(context, [format]).update(view=view, root=root)
    catalog = self._makeDescriberCatalog(context, view, root, options, format)
    ctdef   = self.content_types.get(format)
    return aadict(
      content=self.render(catalog), content_type=ctdef[0], charset=ctdef[1])

  #----------------------------------------------------------------------------
  def _makeDescriberCatalog(self, context, view, root, options, format):
    # todo: filter legend to only those that are actually used?...
    #       => can't do that here since some renderers artificially
    #          re-inject other types.
    legend = [
      (key if (key.lower() + 'Format') not in options else
       options.get(key.lower() + 'Format').format(_('NAME')), desc)
      for key, desc in self.legend]
    catalog = DescriberCatalog(
      describer = self,
      view      = view,
      root      = root,
      format    = format,
      options   = options,
      legend    = legend,
    )
    catalog.typereg   = catalog.options.typereg #.clone()
    # todo: further decorate `context`...
    context = Scope(
      catalog = catalog,
      options = options,
      request = options.context.request,
    )
    # TODO: clone endpoints once caching is enabled
    catalog.endpoints = sorted(
      self.getFilteredEndpoints(options, context), key=lambda e: e.path)
    # TODO: deprecate `catalog.types` (since `catalog.typereg` will be cloned)
    catalog.types     = filter(None, [
      options.tfilters.filter(typ, context=context)
      for typ in catalog.typereg.types()])
    # TODO: re-bind `catalog.endpoints` type references...
    # TODO: re-bind inter-type references...
    catalog = options.cfilters.filter(catalog, context=context)
    return catalog

  #----------------------------------------------------------------------------
  def analyze(self, view):
    # TODO: this is a hack. it was created for unit testing the
    #       numpydoc parsing subsystem... this entire class should be
    #       split into three separate responsibilities:
    #         1. the analyzer: generate a canonical representation of
    #            all `view` endpoints
    #         2. the filter: apply access control
    #            ==> outputs rst? or a doctree? (to avoid round-trip
    #                parsing to extract docorators)
    #            ==> assume rstMax output and let the renderer remove it?
    #         3. the renderer: convert the endpoints to a serialized
    #            representation
    root    = '/'
    context = adict(request=adict())
    options = self._getOptions(context, ['rst']).update(view=view, root=root)
    catalog = self._makeDescriberCatalog(context, view, root, options, format)
    return catalog

  #----------------------------------------------------------------------------
  def _getOptions(self, context, formatstack):
    format = formatstack[0]
    options = adict(self.options[None])
    for idx in range(len(formatstack)):
      options.update(self.options.get('+'.join(formatstack[:1 + idx])))
    if six.callable(context.get_options):
      options.update(context.get_options(format))
    options.update(self.override[None])
    for idx in range(len(formatstack)):
      options.update(self.override.get('+'.join(formatstack[:1 + idx])))
    ret = adict()
    # remove all 'revert-to-default' options
    for key in [key for key, value in options.items() if value == DEFAULT]:
      del options[key]
    # convert the boolean options
    for name, default in self.bool_options:
      ret[name] = asbool(options.get(name, default))
    # convert the integer options
    for name, default in self.int_options:
      try:
        ret[name] = int(options.get(name)) if name in options else default
      except (ValueError, TypeError):
        ret[name] = default
    # convert the list options
    for name, default in self.list_options:
      ret[name] = tolist(options.get(name, default))
    # copy the string options
    for name, default in self.str_options:
      ret[name] = options.get(name, default)
    ret.typereg     = self.typereg
    ret.format      = format
    ret.formatstack = formatstack
    ret.dispatcher  = getDispatcherFromStack() or Dispatcher(autoDecorate=False)
    ret.restVerbs   = set([meth2action(e) for e in ret.restVerbs])
    # todo: a lot of these (especially `render.template`) are monkey-patched
    #       onto the `options`... ugh. these need to be replaced with a more
    #       generalized `context` or `stage` parameter...
    ret.eparsers    = self.eparsers
    ret.tparsers    = self.tparsers
    ret.cparsers    = self.cparsers
    ret.efilters    = self.efilters
    ret.tfilters    = self.tfilters
    ret.cfilters    = self.cfilters
    ret['render.template'] = self.render_template
    ret.renderer    = None
    for idx in range(len(formatstack)):
      fmt = '+'.join(formatstack[:1 + idx])
      if fmt in self.renderers:
        ret.renderer = self.renderers[fmt]
    ret.context     = context
    ret.idEncoder   = tag
    ret.filters     = [resolve(e) for e in ( ret.filters or [] )]
    # TODO: this feels like a hack...
    for prefix in ('type.', 'typereg.', 'access.'):
      ret.update({k: v for k, v in self.settings.items() if k.startswith(prefix)})
    # /TODO
    return ret

  #----------------------------------------------------------------------------
  def getFilteredEndpoints(self, options, context):
    for entry in self.getCachedEndpoints(options):
      if entry.methods:
        entry.methods = filter(None, [
          options.efilters.filter(e, context)
          for e in entry.methods])
      entry = options.efilters.filter(entry, context)
      if entry:
        yield entry

  #----------------------------------------------------------------------------
  def getCachedEndpoints(self, options):
    # TODO: implement caching...
    #       *** IMPORTANT *** when caching is implemented, make sure that
    #       the typereg and the endpoints are cloned pre filtering!...
    # TODO: rearchitect this so that it is shared w _makeDescriberCatalog
    context    = Scope(options=options)
    catalog    = DescriberCatalog(
      options    = options,
      endpoints  = list(self.getEndpoints(options, context)),
      typereg    = options.typereg,
    )
    context.catalog = options.cparsers.filter(catalog, context=context)
    # TODO: ugh. this should really be done *before* catalog filtering,
    #       but currently catalog filtering merges type declarations...
    #       fix!
    for typ in options.typereg.types():
      options.tparsers.filter(typ, context=context)
    return context.catalog.endpoints

  #----------------------------------------------------------------------------
  def getEndpoints(self, options, context):

    if isstr(options.view) and self.settings.config:
      # TODO: is this the "right" way?...
      # TODO: DRY... see cli.py!
      from pyramid.scripts.pviews import PViewsCommand
      pvcomm = PViewsCommand([])
      options.view = pvcomm._find_view(options.view, self.settings.config.registry)

    # todo: remove requirement on a single view...
    if IMultiView.providedBy(options.view):
      options.view = options.view.views[0][1]

    # TODO: add support for any kind of view_callable...
    if not isinstance(options.view, Controller):
      try:
        # TODO: this is *ridiculous*... it is extracting the controller from
        #       the closure... ugh. *obviously* not the right way...
        options.view = options.view.__closure__[1].cell_contents.__wraps__.__closure__[0].cell_contents
        # TODO: handle case where options.view is a subclass (but not instance) of Controller...
        if not isinstance(options.view, Controller):
          raise TypeError('not a controller: %r', options.view)
      except Exception:
        log.exception('invalid target for pyramid-describe: %r', options.view)
        raise TypeError(_('the URL "{}" does not point to a pyramid_controllers.Controller', options.root))
    # todo: further decorate `context`...
    for entry in self._walkEntries(options, None):
      if entry.methods:
        entry.methods = filter(None, [
          options.eparsers.filter(e, context)
          for e in entry.methods])
        entry.methods = sorted(entry.methods, key=self.methOrderKey)
      entry = options.eparsers.filter(entry, context)
      if entry:
        yield entry

  #----------------------------------------------------------------------------
  def _walkEntries(self, options, entry):
    # todo: what about detecting circular references?...
    for ent in self._listAllEntries(options, entry):
      fent = self.filterEntry(options, ent)
      if fent and ( ent.isEndpoint or options.showBranches ):
        yield ent
      # todo: this maxdepth application is inefficient...
      if options.maxdepth is not None \
          and len(list(ent.parents)) >= options.maxdepth:
        continue
      for subent in self._walkEntries(options, ent):
        fsubent = self.filterEntry(options, subent)
        if fsubent and ( subent.isEndpoint or options.showBranches ):
          yield subent

  #----------------------------------------------------------------------------
  def _listAllEntries(self, options, entry):
    if entry is None:
      yield self.controller2entry(options, '', options.view, None)
      return
    if not entry.isController:
      return
    for name, attr in options.dispatcher.getEntries(entry.view, includeIndirect=True):
      if not options.showUnderscore and name.startswith('_'):
        continue
      if options.pruneIndex and name == Dispatcher.NAME_INDEX:
        continue
      # todo: DRY! see dispatcher for sharing...
      if isinstance(attr, Controller):
        subent = self.controller2entry(options, name, attr, entry)
        if subent:
          yield subent
        continue
      # todo: DRY! see dispatcher for sharing...
      if type(attr) in (types.TypeType, types.ClassType):
        subent = self.class2entry(options, name, attr, entry)
        if subent:
          yield subent
        continue
      subent = self.method2entry(options, name, attr, entry)
      if subent:
        yield subent

  #----------------------------------------------------------------------------
  def controller2entry(self, options, name, controller, parent):
    'Creates a describer `Entry` object for the specified Controller instance.'
    ret = Entry(name         = name,
                parent       = parent,
                view         = controller,
                isController = True,
                isEndpoint   = True,
                isStub       = not controller._pyramid_controllers.expose,
                isRest       = isinstance(controller, RestController),
                )
    ret = self.decorateEntry(options, ret)
    for entry in self._listAllEntries(adict(options).update(showRest=True), ret):
      if ret.isRest and entry.isMethod:
        if ret.methods is None:
          ret.methods = []
        ret.methods.append(entry)
        continue
    if ret.isRest:
      ret.isEndpoint = True
    else:
      meta = options.dispatcher.getMeta(controller)
      ret.isEndpoint = bool(meta.index)
      if ret.isEndpoint:
        # todo: this violates the pyramid-controllers boundary... fix!
        ret.isIndex = bool([
          spec
          for handler in meta.index
          for spec in getattr(handler, options.dispatcher.PCATTR).index
          if spec.forceSlash or ( spec.forceSlash is not False
                                  and options.dispatcher.defaultForceSlash )
        ])
    return ret

  #----------------------------------------------------------------------------
  def class2entry(self, options, name, klass, parent):
    'Converts an uninstantiated class to an entry.'
    if not options.showDynamic:
      return None
    ret = Entry(
      name         = name,
      parent       = parent,
      view         = klass,
      isController = True,
      isEndpoint   = True,
      isDynamic    = True,
    )
    return self.decorateEntry(options, ret)

  #----------------------------------------------------------------------------
  def method2entry(self, options, name, method, parent):
    'Converts an object method to an entry.'
    ret = Entry(
      name         = name,
      parent       = parent,
      view         = method,
      isController = False,
      isEndpoint   = True,
    )
    if parent and isinstance(parent.view, RestController) \
        and name in options.restVerbs:
      if not options.showRest:
        return None
      ret.method     = action2meth(name)
      ret.isRest     = True
      ret.isMethod   = True
      ret.isEndpoint = False
    return self.decorateEntry(options, ret)

  #----------------------------------------------------------------------------
  def filterEntry(self, options, entry):
    '''
    Checks to see if the specified `entry` should be included in the
    output. The returned object should either be the `entry`
    (potentially modified) or ``None``. In the latter case, the entry
    will be removed from the output.
    '''
    if self.include:
      match = False
      for include in self.include:
        if include.match(entry.path):
          match = True
          break
      if not match:
        return None
    if self.exclude:
      for exclude in self.exclude:
        if exclude.match(entry.path):
          return None
    return entry

  #----------------------------------------------------------------------------
  def decorateEntry(self, options, entry):
    '''
    Decorates the entry with additional attributes that may be useful
    in rendering the final output. Specifically, the following
    attributes are populated as and if possible:

    * `id`:    a document-unique ID for the entry.
    * `path`:  full path to the entry.
    * `dpath`: the full "decorated" path to the entry.
    * `ipath`: the full resolver path to the class or method.
    * `doc`:   the docstring for the entry or the index (see pruneIndex).

    Sub-classes may override & extend this functionality - noting that
    the returned object can either be the original decorated `entry`
    or a new one, in which case it will take the place of the passed-in
    entry.

    See :class:`pyramid_describer.entry.Entry` for details on built-in
    provided attributes, and the list of attributes that are recognized
    but cannot be provided by the default implementation.
    '''

    # determine the implementation path & type to this entry
    if entry.isController:
      kls = entry.view
      entry.itype = 'class' if inspect.isclass(kls) else 'instance'
      if entry.itype == 'instance':
        kls = kls.__class__
      entry.ipath = kls.__module__ + '.' + kls.__name__
    else:
      if inspect.ismethod(entry.view):
        entry.ipath = inspect.getmodule(entry.view).__name__ \
            + '.' + entry.view.__self__.__class__.__name__ \
            + '().' + entry.view.__name__
        entry.itype = 'method'
      elif inspect.isfunction(entry.view):
        entry.ipath = inspect.getmodule(entry.view).__name__ \
            + '.' + entry.view.__name__
        entry.itype = 'function'
      else:
        entry.ipath = entry.view.__name__
        entry.itype = 'unknown'

    # determine the "decorated" path
    if entry.isStub:
      entry.dname = options.stubFormat.format(entry.name)
    elif entry.isDynamic:
      entry.dname = options.dynamicFormat.format(entry.name)
    elif entry.isMethod:
      entry.dname = options.restFormat.format(entry.method)
    else:
      entry.dname = entry.name

    # determine the full path (plain and "decorated") to this entry
    if not entry.parent:
      entry.path  = options.root
      entry.dpath = options.root
    else:
      entry.path  = entry.parent.path
      entry.dpath = entry.parent.dpath
    if entry.isMethod:
      entry.path  = entry.path + '?_method=' + urllib.parse.quote(entry.method or entry.name)
      entry.dpath = entry.dpath + '?_method=' + urllib.parse.quote(entry.method or entry.name)
    else:
      if not entry.path.endswith('/'):
        entry.path += '/'
      if not entry.dpath.endswith('/'):
        entry.dpath += '/'
      entry.path  += entry.name
      entry.dpath += entry.dname

    # generate an ID
    if entry.isMethod:
      entry.id = 'method-{}-{}'.format(
        tag(entry.path[:entry.path.find('?_method=')]),
        tag(entry.method or entry.name))
    else:
      entry.id = 'endpoint-{}'.format(tag(entry.path))

    # get the docstring
    entry.doc = inspect.getdoc(entry.view)
    if options.pruneIndex and entry.isController:
      meta = options.dispatcher.getMeta(entry.view)
      for handler in meta.index or []:
        entry.doc = inspect.getdoc(handler) or entry.doc

    return entry

  #----------------------------------------------------------------------------
  def structure_entry(self, options, entry, dentry, dict=dict):
    if entry.params is not None:
      dentry['params'] = entry.params.tostruct(ref=True)
    if entry.returns is not None:
      dentry['returns'] = entry.returns.tostruct(ref=True)
    if entry.raises is not None:
      dentry['raises'] = entry.raises.tostruct(ref=True)
    if options.showExtra and entry.extra:
      try:
        for k, v in entry.extra.items():
          if v is None:
            dentry.pop(k, None)
          else:
            dentry[k] = v
      except AttributeError: pass
    return dentry

  #----------------------------------------------------------------------------
  def structure_render(self, catalog, dict=dict, includeEntry=False):
    root = dict(application=dict(url=catalog.options.context.request.host_url))
    app = root['application']
    if catalog.endpoints:
      app['endpoints'] = []
    for entry in catalog.endpoints:
      endpoint = dict(path=entry.path)
      if catalog.options.showIds:
        endpoint['id'] = entry.id
      if catalog.options.showName:
        endpoint['name'] = entry.name
      if catalog.options.showDecorated:
        if catalog.options.showName:
          endpoint['decoratedName'] = entry.dname
        endpoint['decoratedPath'] = entry.dpath
      if includeEntry:
        endpoint['entry'] = entry
      if catalog.options.showInfo and entry.doc:
        endpoint['doc'] = entry.doc
      if catalog.options.showMethods and entry.methods:
        endpoint['methods'] = []
        for meth in entry.methods:
          dmeth = dict(name=meth.method)
          if catalog.options.showIds and meth.id:
            dmeth['id'] = meth.id
          if meth.doc:
            dmeth['doc'] = meth.doc
          if includeEntry:
            dmeth['entry'] = meth
          endpoint['methods'].append(self.structure_entry(catalog.options, meth, dmeth, dict=dict))
      if catalog.options.showExtra and entry.extra:
        try:
          for k, v in entry.extra.items():
            if v is None:
              endpoint.pop(k, None)
            else:
              endpoint[k] = v
        except AttributeError: pass
      app['endpoints'].append(endpoint)
      tnames = catalog.typereg.typeNames()
      if tnames:
        app['types'] = [
          catalog.typereg.get(name).tostruct() for name in tnames]

    # todo: filter...
    # todo: what about formatting `doc`...
    #       ==> especially paragraph & title docorator extraction...

    return root

  #----------------------------------------------------------------------------
  def template_render(self, catalog):
    tpl = catalog.options.renderer \
      or 'pyramid_describe:template/' + catalog.format + '.mako'
    return pyramid_render(
      tpl, dict(data=catalog), request=catalog.options.context.request)

  #----------------------------------------------------------------------------
  def doctree_render(self, catalog):
    if catalog.options.get('render.template', None) is not None:
      return render.render(catalog, catalog.options.get('render.template'))
    return doctree.render(catalog)

  #----------------------------------------------------------------------------
  def render(self, data, format=None, override_options=None):
    if format is not None:
      # todo: this is *ugly*... basically, the problem is that data.options
      #       is format-specific, and therefore i need to regenerate one if
      #       it is changed. ugh.
      keep_fmt = data.format
      keep_opt = data.options
      formatstack = [format] + data.options.formatstack
      data.format = format
      data.options = self._getOptions(keep_opt.context, formatstack).update(
        view=keep_opt.view, root=keep_opt.root)
      if override_options:
        data.options.update(override_options)
      ret = self.render(data)
      data.format  = keep_fmt
      data.options = keep_opt
      return ret
    return getattr(self, 'render_' + data.format, self.template_render)(data)

  #----------------------------------------------------------------------------
  def render_rst(self, data):
    doc = self.doctree_render(data)
    # todo: should this runFilters be moved int doctree_render?...
    #       currently it is only being called from here, so not much
    #       of an issue, but if ever it isn't, then this behaviour might
    #       not be expected.
    doc = runFilters(data.options.filters, doc, data)
    writer = resolve(data.options.rstWriter)()
    settings = dict(
      doctitle_xform       = False,
      sectsubtitle_xform   = False,
    )
    if data.options.rstMax:
      settings['explicit_title'] = True
    return publish_from_doctree(
      doc, writer=writer, settings_overrides=settings)

  #----------------------------------------------------------------------------
  render_txt = template_render

  #----------------------------------------------------------------------------
  def render_html(self, data):
    text = self.render(data, format='rst', override_options=dict({
      'rstMax': True,
    }))
    return rst.rst2html(data, text)

  #----------------------------------------------------------------------------
  def render_pdf(self, data):
    if not pdfkit:
      raise ValueError('pdfkit not available')
    html = self.render(data, format='html').decode('UTF-8')
    pdf  = pdfkit.from_string(html, False, options={'quiet': None})
    if len(pdf.strip()) <= 0:
      raise ValueError(
        'pdfkit failed to generate a PDF - usually a "pdfkit.options" problem')
    return pdf

  #----------------------------------------------------------------------------
  def render_json(self, data):
    return json.dumps(self.structure_render(data))

  #----------------------------------------------------------------------------
  def render_yaml(self, data):
    return yaml.dump(self.structure_render(data))

  #----------------------------------------------------------------------------
  def render_xml(self, catalog):
    # todo: move to asset.plugin-oriented format loading and handling... ie:
    #   in __init__:
    #     self.renderers = asset.plugins(
    #       'pyramid_describe.plugins.renderers',
    #       self.settings.get('renderers', '*'))
    #   then here:
    #     return self.renderers.select('xml').handle(data)
    from .renderer import xml
    return xml.render(catalog)

  #----------------------------------------------------------------------------
  def render_wadl(self, catalog):
    # todo: see `render_xml`, then:
    #   return self.renderers.select('wadl').handle(data)
    from .renderer import wadl
    return wadl.render(catalog)


#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
