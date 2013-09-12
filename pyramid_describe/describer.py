# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2013/09/10
# copy: (C) Copyright 2013 Cadit Health Inc., All Rights Reserved.
#------------------------------------------------------------------------------

import re, logging, inspect, binascii, types
from six.moves import urllib
from pyramid.interfaces import IMultiView
from pyramid.settings import asbool, aslist
from pyramid.renderers import render
from pyramid_controllers import Controller, RestController, Dispatcher
from pyramid_controllers.restcontroller import meth2action, action2meth, HTTP_METHODS
from pyramid_controllers.dispatcher import getDispatcherFromStack

from .entry import Entry
from .util import adict, isstr, resolve
from .i18n import _

log = logging.getLogger(__name__)

try:
  import yaml
  FORMATS = ('html', 'txt', 'rst', 'json', 'yaml', 'wadl', 'xml')
except ImportError:
  FORMATS = ('html', 'txt', 'rst', 'json', 'wadl', 'xml')

#------------------------------------------------------------------------------
def entcmp(e1, e2):
  if e1.parent is not e2.parent:
    return cmp(e1.path, e2.path)
  r1 = bool(e1.isMethod)
  r2 = bool(e2.isMethod)
  if r1 == r2:
    return cmp(e1.name, e2.name)
  if r1:
    return -1
  return 1

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
    #for entry in sorted(list(self.endpoints), cmp=entcmp):
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
pue_re   = re.compile('[^a-zA-Z0-9]')
def pue_repl(match):
  return '_' + binascii.hexlify(match.group(0)).upper()
def pseudoUrlEncode(text):
  return pue_re.sub(pue_repl, text)

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
     _('Dynamically evaluated endpoint, so no further information can be'
       ' determined without specific contextual request details.')),
    (Dispatcher.NAME_DEFAULT,
     _('This endpoint is a `default` handler, and is therefore free to interpret'
       ' path arguments dynamically, so no further information can be determined'
       ' without specific contextual request details.')),
    (Dispatcher.NAME_LOOKUP,
     _('This endpoint is a `lookup` handler, and is therefore free to interpret'
       ' path arguments dynamically, so no further information can be determined'
       ' without specific contextual request details.')),
    )

  bool_options = (
    ('showUnderscore', False),
    ('showUndoc',      True),
    ('showLegend',     True),
    ('showBranches',   False),
    ('pruneIndex',     True),
    ('showRest',       True),
    ('showImpl',       False),
    ('showInfo',       True),
    ('showExtra',      True),
    ('showMethods',    True),
    ('showIds',        True),
    ('showDynamic',    True),
    ('showGenerator',  True),
    ('showGenVersion', True),
    ('showLocation',   True),
    ('ascii',          False),
    )

  int_options = (
    ('maxdepth',       1024),
    ('width',          79),
    ('maxDocColumn',   None),
    ('minDocLength',   20),
    )

  list_options = (
    ('restVerbs',      HTTP_METHODS),
    )

  str_options = (
    ('stubFormat',    '{{{}}}'),     # /path/to/{NAME}/and/more
    ('dynamicFormat', '{}/?'),       # /path/to/NAME/?
    ('restFormat',    '<{}>'),       # /path/to/<NAME>
    )

  #----------------------------------------------------------------------------
  def __init__(self, settings=None, default=None, override=None):
    self.settings  = adict(settings or dict())
    self.include   = [re.compile(expr) if isstr(expr) else expr
                      for expr in aslist(self.settings.include or '')]
    self.exclude   = [re.compile(expr) if isstr(expr) else expr
                      for expr in aslist(self.settings.exclude or '')]
    self.formats   = aslist(self.settings.formats or '') or FORMATS
    self.defformat = self.settings.get('format.default', self.formats[0])
    self.options   = extract(self.settings, 'format.default')
    self.options.update(default or dict())
    self.override  = extract(self.settings, 'format.override')
    self.override.update(override or dict())
    for format in self.formats:
      setattr(self, 'options_' + format, extract(self.settings, 'format.' + format + '.default'))
      setattr(self, 'override_' + format, extract(self.settings, 'format.' + format + '.override'))
    self.filters   = []
    if self.settings.filters:
      try:
        self.filters = aslist(self.settings.filters)
      except TypeError:
        try:
          self.filters = [filt for filt in self.settings.filters]
        except TypeError:
          self.filters = [self.settings.filters]
      self.filters = [resolve(e) for e in self.filters]

  #----------------------------------------------------------------------------
  def describe(self, view, request, format=None, root=None):
    if request is None:
      request = adict(params=adict())
    if format is None:
      format = request.params.get('format', None)
    if format is None:
      format = self.defformat
    options = self._getOptions(request, format)
    options.view = view
    options.root = root
    # todo: filter legend to only those that are actually used?...
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
    renderer = getattr(self, 'render_' + format, self.template_render)
    return renderer(request, data)

  #----------------------------------------------------------------------------
  def _getOptions(self, request, format):
    options = adict(self.options)
    options.update(getattr(self, 'options_' + format, None))
    options.update(getattr(request, 'options', None))
    options.update(request.params)
    options.update(getattr(request, 'override', None))
    options.update(self.override)
    options.update(getattr(self, 'override_' + format, None))
    ret = adict()
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
      ret[name] = aslist(options.get(name, default))
    # copy the string options
    for name, default in self.str_options:
      ret[name] = options.get(name, default)
    ret.format     = format
    ret.request    = request
    ret.dispatcher = getDispatcherFromStack() or Dispatcher(autoDecorate=False)
    ret.restVerbs  = set([meth2action(e) for e in ret.restVerbs])
    ret.filters    = self.filters
    return ret

  #----------------------------------------------------------------------------
  def _filter(self, options, entry):
    if not entry:
      return None
    for efilter in options.filters:
      entry = efilter(entry)
      if not entry:
        break
    return entry

  #----------------------------------------------------------------------------
  def get_endpoints(self, options):

    # todo: remove requirement on a single view...
    if IMultiView.providedBy(options.view):
      options.view = options.view.views[0][1]

    # TODO: add support for any kind of view_callable...
    if not isinstance(options.view, Controller):
      try:
        # TODO: this is *ridiculous*... it is extracting the controller from
        #       the closure... ugh. *obviously* not the right way...
        options.view = options.view.__closure__[1].cell_contents.__wraps__.__closure__[0].cell_contents
        if not isinstance(options.view, Controller):
          raise TypeError('not a controller: %r', options.view)
      except Exception:
        log.exception('invalid target for pyramid-describe: %r', options.view)
        raise TypeError(_('the URL "{}" does not point to a pyramid_controllers.Controller', options.root))

    for entry in self._walkEntries(options, None):
      if entry.methods:
        entry.methods = filter(None, [self._filter(options, e) for e in entry.methods])
      entry = self._filter(options, entry)
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

    Although the default :class:`Describer` does not extract or
    otherwise determine any attributes beyond the above specified
    attributes, there are additional attributes that some of the
    formatters will take advantage of. For this reason, sub-classes
    are encouraged to further decorate the entries where possible with
    the following attributes:

    * `params`: a list of objects that represent parameters that this
      entry accepts. The objects can have the following attributes:
      `name`, `type`, `optional`, `default`, and `doc`.

    * `returns`: a list of objects that documents the return values
      that can be expected from this method. The objects can have the
      following attributes: `type` and `doc`.

    * `raises`: a list of objects that specify what exceptions this
      method can raise. The objects can have the following attributes:
      `type` and `doc`.

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
        self._encodeIdComponent(entry.path[:entry.path.find('?_method=')]),
        self._encodeIdComponent(entry.method or entry.name))
    else:
      entry.id = 'endpoint-{}'.format(self._encodeIdComponent(entry.path))

    # get the docstring
    if options.showInfo:
      entry.doc = inspect.getdoc(entry.view)
      if options.pruneIndex and entry.isController:
        meta = options.dispatcher.getMeta(entry.view)
        for handler in meta.index or []:
          entry.doc = inspect.getdoc(handler) or entry.doc

    return entry

  #----------------------------------------------------------------------------
  def _encodeIdComponent(self, text):
    return pseudoUrlEncode(text)

  #----------------------------------------------------------------------------
  def template_render(self, request, data):
    return render('pyramid_describe:template/' + data.format + '.mako',
                  dict(data=data), request=request)

  render_html = template_render
  render_txt  = template_render

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
