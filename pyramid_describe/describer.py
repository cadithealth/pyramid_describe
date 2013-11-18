# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2013/09/10
# copy: (C) Copyright 2013 Cadit Health Inc., All Rights Reserved.
#------------------------------------------------------------------------------

import re, logging, inspect, binascii, types, json, six, collections
from six.moves import urllib
import xml.etree.ElementTree as ET
try:
  import yaml
except ImportError:
  yaml = None
from docutils.core import publish_doctree, publish_from_doctree
from pyramid.interfaces import IMultiView
from pyramid.settings import asbool, truthy
from pyramid.renderers import render
from pyramid_controllers import Controller, RestController, Dispatcher
from pyramid_controllers.restcontroller import meth2action, action2meth, HTTP_METHODS
from pyramid_controllers.dispatcher import getDispatcherFromStack

from .entry import Entry
from .util import adict, isstr, tolist, resolve, pick, reparse, runFilters, tag
from . import rst, doctree
from .i18n import _

log = logging.getLogger(__name__)

DEFAULT = 'pyramid_describe:DEFAULT'
FORMATS = ('html', 'txt', 'rst', 'json', 'wadl', 'xml')

try:
  import yaml
  FORMATS += ('yaml',)
except ImportError: pass

try:
  import pdfkit
  FORMATS += ('pdf',)
except ImportError: pass

#------------------------------------------------------------------------------
def ccc(name):
  'Convert Camel Case (converts camelCase to camel-case).'
  def repl(match):
    return match.group(1) + '-' + match.group(2).lower()
  return re.sub('([a-z])([A-Z])', repl, name)
def singular(name):
  if name.endswith('s'):
    return name[:-1]
  return name
def isscalar(obj):
  return isinstance(obj, six.string_types + (bool, int, float))
def islist(obj):
  if isscalar(obj) or isinstance(obj, dict):
    return False
  try:
    list(obj)
    return True
  except TypeError:
    return False

#------------------------------------------------------------------------------
def add2node(obj, node):
  if obj is None:
    return
  if isscalar(obj):
    node.text = ( node.text or '' ) + str(obj)
    return
  if isinstance(obj, dict):
    for k, v in obj.items():
      if v is None:
        continue
      if isscalar(v):
        node.set(ccc(k), str(v))
        continue
      if islist(v):
        # todo: this 'singularization' should probably be in render_xml...
        k = singular(k)
        for el in v:
          node.append(dict2node(dict([(k,el)])))
        continue
      node.append(dict2node(dict([(k,v)])))
    return
  raise NotImplementedError()

#------------------------------------------------------------------------------
def dict2node(d):
  if len(d) != 1:
    node = ET.Element('element')
    for k, v in d.items():
      node.append(dict2node(dict([(k, v)])))
    return node
  node = ET.Element(ccc(d.keys()[0]))
  add2node(d.values()[0], node)
  return node

#------------------------------------------------------------------------------
def et2str(data):
  return ET.tostring(data, 'UTF-8').replace(
    '<?xml version=\'1.0\' encoding=\'UTF-8\'?>',
    '<?xml version="1.0" encoding="UTF-8"?>')

#------------------------------------------------------------------------------
class DescriberData(adict):
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
        for method in sorted(entry.methods, key=lambda e: e.name):
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
class Describer(object):

  xmlns = dict(
    wadl = 'http://research.sun.com/wadl/2006/10',
    xsd  = 'http://www.w3.org/2001/XMLSchema',
    xsi  = 'http://www.w3.org/2001/XMLSchema-instance',
    doc  = 'http://pythonhosted.org/pyramid_describer/xmlns/0.1/doc',
    )

  wadl_type_remap = {
    'bool':  'xsd:boolean',
    'int':   'xsd:integer',
    'float': 'xsd:float',
    'str':   'xsd:string',
    }

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
    'html': ('text/html', 'UTF-8'),
    'json': ('application/json', 'UTF-8'),
    'pdf':  ('application/pdf', 'UTF-8'),
    'rst':  ('text/x-rst', 'UTF-8'),
    'txt':  ('text/plain', 'UTF-8'),
    'wadl': ('text/xml', 'UTF-8'),
    'xml':  ('text/xml', 'UTF-8'),
    'yaml': ('application/yaml', 'UTF-8'),
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
    ('showOutline',    True),
    ('pageGrayscale',  False),
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
    ('title',            None),
    ('endpoints.title',  None),
    ('legend.title',     None),
    ('stubFormat',       '{{{}}}'),     # /path/to/{NAME}/and/more
    ('dynamicFormat',    '{}/?'),       # /path/to/NAME/?
    ('restFormat',       '<{}>'),       # /path/to/<NAME>
    ('pageSize',         'A4'),
    ('pageOrientation',  'Portrait'),
    ('pageMarginTop',    '10mm'),
    ('pageMarginRight',  '10mm'),
    ('pageMarginBottom', '10mm'),
    ('pageMarginLeft',   '10mm'),
    ('cssPath',          'pyramid_describe:template/rst2html.css'),
    ('encoding',         'UTF-8'),
    ('rstWriter',        'pyramid_describe.writers.rst.Writer'),
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
    # and now load the entry filters
    self.efilters   = self.settings.get('entries.filters', [])
    if self.efilters:
      try:
        self.efilters = tolist(self.efilters)
      except TypeError:
        try:
          self.efilters = [filt for filt in self.efilters]
        except TypeError:
          self.efilters = [self.efilters]
      self.efilters = [resolve(e) for e in self.efilters]

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
    # todo: filter legend to only those that are actually used?...
    #       => can't do that here since some renderers artificially
    #          re-inject other types.
    legend = [
      (key if (key.lower() + 'Format') not in options else
       options.get(key.lower() + 'Format').format(_('NAME')), desc)
      for key, desc in self.legend]
    data = DescriberData(
      view      = view,
      root      = root,
      format    = format,
      options   = options,
      endpoints = sorted(self.get_endpoints(options), key=lambda e: e.path),
      legend    = legend,
      )
    ctdef = self.content_types.get(format)
    return adict(content=self.render(data), content_type=ctdef[0], charset=ctdef[1])

  #----------------------------------------------------------------------------
  def _getOptions(self, context, formatstack):
    format = formatstack[0]
    options = adict(self.options[None])
    for idx in range(len(formatstack)):
      options.update(self.options.get('+'.join(formatstack[:1 + idx])))
    if callable(context.get_options):
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
    ret.format      = format
    ret.formatstack = formatstack
    ret.dispatcher  = getDispatcherFromStack() or Dispatcher(autoDecorate=False)
    ret.restVerbs   = set([meth2action(e) for e in ret.restVerbs])
    ret.efilters    = self.efilters
    ret.renderer    = None
    for idx in range(len(formatstack)):
      fmt = '+'.join(formatstack[:1 + idx])
      if fmt in self.renderers:
        ret.renderer = self.renderers[fmt]
    ret.context     = context
    ret.idEncoder   = tag
    ret.filters     = [resolve(e) for e in ( ret.filters or [] )]
    return ret

  #----------------------------------------------------------------------------
  def get_endpoints(self, options):

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

    for entry in self._walkEntries(options, None):
      if entry.methods:
        entry.methods = filter(None, [
          runFilters(options.efilters, e, options)
          for e in entry.methods])
      entry = runFilters(options.efilters, entry, options)
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
    ret = Entry(name         = name,
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
    ret = Entry(name         = name,
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
  def _pick_param(self, options, value):
    if options.showIds:
      return pick(value, 'id', 'name', 'type', 'optional', 'default', 'doc')
    return pick(value, 'name', 'type', 'optional', 'default', 'doc')

  #----------------------------------------------------------------------------
  def _pick_return(self, options, value):
    if options.showIds:
      return pick(value, 'id', 'type', 'doc')
    return pick(value, 'type', 'doc')

  #----------------------------------------------------------------------------
  def _pick_raise(self, options, value):
    if options.showIds:
      return pick(value, 'id', 'type', 'doc')
    return pick(value, 'type', 'doc')

  #----------------------------------------------------------------------------
  def structure_entry(self, options, entry, dentry, dict=dict):
    if entry.params is not None:
      dentry['params'] = [
        dict(self._pick_param(options, e))
        for e in entry.params]
    if entry.returns is not None:
      dentry['returns'] = [dict(self._pick_return(options, e)) for e in entry.returns]
    if entry.raises is not None:
      dentry['raises'] = [dict(self._pick_raise(options, e)) for e in entry.raises]
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
  def structure_render(self, data, dict=dict, includeEntry=False):
    root = dict(application=dict(url=data.options.context.request.host_url))
    app = root['application']
    app['endpoints'] = []
    for entry in data.endpoints:
      endpoint = dict(path=entry.path)
      if data.options.showIds:
        endpoint['id'] = entry.id
      if data.options.showName:
        endpoint['name'] = entry.name
      if data.options.showDecorated:
        if data.options.showName:
          endpoint['decoratedName'] = entry.dname
        endpoint['decoratedPath'] = entry.dpath
      if includeEntry:
        endpoint['entry'] = entry
      if data.options.showInfo and entry.doc:
        endpoint['doc'] = entry.doc
      if data.options.showMethods and entry.methods:
        endpoint['methods'] = []
        for meth in entry.methods:
          dmeth = dict(name=meth.method)
          if data.options.showIds and meth.id:
            dmeth['id'] = meth.id
          if meth.doc:
            dmeth['doc'] = meth.doc
          if includeEntry:
            dmeth['entry'] = meth
          endpoint['methods'].append(self.structure_entry(data.options, meth, dmeth, dict=dict))
      if data.options.showExtra and entry.extra:
        try:
          for k, v in entry.extra.items():
            if v is None:
              endpoint.pop(k, None)
            else:
              endpoint[k] = v
        except AttributeError: pass
      app['endpoints'].append(endpoint)

    # filter...

    return root

  #----------------------------------------------------------------------------
  def template_render(self, data):
    tpl = data.options.renderer \
      or 'pyramid_describe:template/' + data.format + '.mako'
    return render(tpl, dict(data=data), request=data.options.context.request)

  #----------------------------------------------------------------------------
  def doctree_render(self, data):
    return doctree.render(data)

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
    html = self.render(data, format='html').decode('UTF-8')
    return pdfkit.from_string(html, False, options={'quiet': ''})

  #----------------------------------------------------------------------------
  def render_json(self, data):
    return json.dumps(self.structure_render(data))

  #----------------------------------------------------------------------------
  def render_yaml(self, data):
    if yaml is None:
      raise ValueError('no yaml encoder library available')
    return yaml.dump(self.structure_render(data))

  #----------------------------------------------------------------------------
  def render_xml(self, data):
    data = self.structure_render(data, dict=collections.OrderedDict)
    # force 'doc' attribute into a list, which causes dict2node to
    # make it into a node instead of an attribute
    def doc2list(node):
      if isscalar(node) or node is None:
        return
      if islist(node):
        for sub in node:
          doc2list(sub)
        return
      if 'doc' in node:
        node['doc'] = [node['doc']]
      for value in node.values():
        doc2list(value)
    doc2list(data)
    return et2str(dict2node(data))

  #----------------------------------------------------------------------------
  def et2wadl(self, options, root):
    for ns, uri in self.xmlns.items():
      if ns == 'wadl':
        root.set('xmlns', uri)
      else:
        root.set('xmlns:' + ns, uri)
    root.set('xsi:schemaLocation', self.xmlns['wadl'] + ' wadl.xsd')
    rename = {
      'doc':       'doc:doc',
      'endpoint':  'resource',
      'return':    'representation',
      'raise':     'fault',
      }
    resources = ET.Element('resources')
    for elem in list(root):
      root.remove(elem)
      resources.append(elem)
    root.append(resources)
    appUrl = None
    for elem in root.iter():
      if elem.tag in rename:
        elem.tag = rename[elem.tag]
      if elem.tag == 'application' and 'url' in elem.attrib:
        appUrl = elem.attrib.pop('url')
      if elem.tag == 'resources' and appUrl:
        elem.set('base', appUrl)
      elem.attrib.pop('decorated-name', None)
      elem.attrib.pop('decorated-path', None)
      if 'path' in elem.attrib and elem.attrib.get('path').startswith('/'):
        elem.attrib['path'] = elem.attrib.get('path')[1:]
      if elem.tag == 'resource':
        elem.attrib.pop('name', None)
      if elem.tag == 'method':
        reqnodes = []
        resnodes = []
        for child in list(elem):
          if child.tag in ('param',):
            reqnodes.append(child)
            elem.remove(child)
          elif child.tag in ('return', 'raise'):
            resnodes.append(child)
            elem.remove(child)
        if reqnodes:
          req = ET.SubElement(elem, 'request')
          req.extend(reqnodes)
        if resnodes:
          res = ET.SubElement(elem, 'response')
          res.extend(resnodes)
      if elem.tag == 'representation':
        if 'type' in elem.attrib:
          val = elem.attrib.pop('type')
          elem.attrib['element'] = self.wadl_type_remap.get(val, val)
        if 'doc' in elem.attrib:
          doc = elem.attrib.pop('doc')
          ET.SubElement(elem, 'doc:doc').text = doc
      if elem.tag == 'param':
        if 'optional' in elem.attrib:
          opt = asbool(elem.attrib.pop('optional'))
          elem.attrib['required'] = 'true' if not opt else 'false'
        if 'type' in elem.attrib:
          val = elem.attrib['type']
          if val in self.wadl_type_remap:
            elem.attrib['type'] = self.wadl_type_remap[val]
        if 'doc' in elem.attrib:
          doc = elem.attrib.pop('doc')
          ET.SubElement(elem, 'doc:doc').text = doc
      if elem.tag == 'fault':
        doc = elem.attrib.pop('doc', None)
        if doc:
          ET.SubElement(elem, 'doc:doc').text = doc
        if 'type' in elem.attrib:
          val = elem.attrib.pop('type')
          elem.attrib['element'] = self.wadl_type_remap.get(val, val)
    return root

  #----------------------------------------------------------------------------
  def render_wadl(self, data):
    options = data.options
    data = self.structure_render(data, dict=collections.OrderedDict)
    # force 'doc' attribute into a list, which causes dict2node to
    # make it into a node instead of an attribute
    def doc2list(node):
      if isscalar(node) or node is None:
        return
      if islist(node):
        for sub in node:
          doc2list(sub)
        return
      if 'doc' in node:
        node['doc'] = [node['doc']]
      for value in node.values():
        doc2list(value)
    doc2list(data)
    # force all endpoints to have at least a 'GET' method
    for endpoint in data['application']['endpoints']:
      if not endpoint.get('methods'):
        endpoint['methods'] = [dict(
          id='method-{}-{}'.format(tag(endpoint['path']), tag('GET')),
          name='GET')]
    data = dict2node(data)
    data = self.et2wadl(options, data)
    return et2str(data)

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
