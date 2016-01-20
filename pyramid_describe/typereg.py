# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2015/12/01
# copy: (C) Copyright 2015-EOT Cadit Inc., All Rights Reserved.
#------------------------------------------------------------------------------

import logging
import re
import json
import types
import inspect
import copy

import yaml
import six
from aadict import aadict
import asset
import pyramid.httpexceptions
import morph

from .scope import Scope
from .i18n import _

#------------------------------------------------------------------------------

log = logging.getLogger(__name__)

# TODO: here, ``scalar`` really means ``primitive``... replace.
# todo: should `union` really exist?... it was only implemented for
#       "symmetry"...
#       ==> perhapse the "union" name is also a bit misleading???
#           in XMLSchema, "xsd:union" means the same as "one-of" here... ugh.

#------------------------------------------------------------------------------
class _aadict(aadict):
  def __setattr__(self, key, value):
    if value is None:
      return self.__delattr__(key)
    return super(_aadict, self).__setattr__(key, value)
  def __eq__(self, target): return self.__cmp__(target) == 0
  def __ne__(self, target): return self.__cmp__(target) != 0
  def __lt__(self, target): return self.__cmp__(target) < 0
  def __le__(self, target): return self.__cmp__(target) <= 0
  def __gt__(self, target): return self.__cmp__(target) > 0
  def __ge__(self, target): return self.__cmp__(target) >= 0

#------------------------------------------------------------------------------
class Type(_aadict):
  '''
  Represents a complex type definition. Types can have the following
  attributes:

  :Attributes:

  name : str

    The name of the type.

  doc : str, optional, default: null

    A description of the type.

  base : str

    This type's base type, which can be one of:

    * `Type.SCALAR` (``scalar``)
    * `Type.COMPOUND` (``compound``)
    * `Type.LIST` (``list``)
    * `Type.DICT` (``dict``)
    * `Type.CONSTANT` (``constant``)
    * `Type.UNKNOWN` (``unknown``)
    * `Type.EXTENSION` (``extension``)

  value : any, default: null

    Additional type information for `constant` and `compound`
    types. The `value` itself that depends on type, as follows:

    * dict: a list of TypeRef's.
    * list: the type of item that this list comprises.
    * oneof: a list of alternate Type's.
    * union: a list of required Type's.
    * constant: the value of the constant, e.g. ``"female"``.
    * extension: a TypeRef.

  children : iterator

    This is a "helper" attribute that returns an iterator of compound
    types' `value`. For `list` types, this will only yield one
    value. For non-compound types, this will not yield anything.

    IMPORTANT: for some reason, the `children` setter does not seem
    to work as expected... use `Type.setChildren` instead.

    The `children` attribute is "settable". For inappropriate types
    (e.g. scalar types), setting it will be ignored.

  meta : aadict, default: {}

    TODO: this is not actually implemented!

    Some meta-information about the type. **All** values are
    optional. Currently, the following are used by `pyramid_describe`,
    but this may change and is also available for external libraries
    to use as needed:

    * ``referenced``: a list of endpoints where this type is referenced
    * ``defined``: a list of endpoints where this type is defined
    * ``source``: where this type was defined (extensions only)
    * ``classes``: a list of classes to augment this type's rendering

    Note that meta-information is ignored when comparing Type's for
    equality.

  TODO: there is a bit of a "peculiarity" that extension types have a
  `value` of TypeRef... (instead of Type). this is because "params"
  need to be stored somewhere, but Type's don't *have* params.
  probably better would be to store the Type in `base` and put the
  params in `value`...

  '''

  SCALAR        = 'scalar'
  COMPOUND      = 'compound'
  LIST          = 'list'
  DICT          = 'dict'
  ONEOF         = 'oneof'
  UNION         = 'union'
  REF           = 'ref'
  CONSTANT      = 'constant'
  EXTENSION     = 'extension'
  UNKNOWN       = 'unknown'

  ANY           = 'any'
  BYTE          = 'byte'
  BYTES         = 'bytes'
  BOOLEAN       = 'boolean'
  INTEGER       = 'integer'
  NUMBER        = 'number'
  STRING        = 'string'
  NULL          = 'null'

  #----------------------------------------------------------------------------
  def __init__(self, base=None, name=None, doc=None, value=None, meta=None, *args, **kw):

    # TODO: enable this...
    # if not base:
    #   raise ValueError('type "base" parameter is required')
    # if not name:
    #   raise ValueError('type "name" parameter is required')
    if base:
      kw['base'] = base
    if name:
      kw['name'] = name

    if doc:
      kw['doc'] = doc
    if value:
      kw['value'] = value
    kw['meta'] = aadict(meta or {})
    super(Type, self).__init__(*args, **kw)

  #----------------------------------------------------------------------------
  def clone(self):
    value = copy.deepcopy(self.value)
    meta  = copy.deepcopy(self.meta)
    return Type(
      base=self.base, name=self.name, doc=self.doc, value=value, meta=meta)

  #----------------------------------------------------------------------------
  @property
  def children(self):
    if self.value is None or self.value == []:
      return
    if isinstance(self.value, (Type, TypeRef)):
      if isinstance(self.value, (Type, TypeRef)):
        yield self.value
      return
    if isinstance(self.value, (list, tuple)):
      for item in self.value:
        if isinstance(item, (Type, TypeRef)):
          yield item
      return

  #----------------------------------------------------------------------------
  def is_dict(self):
    return self.base == Type.COMPOUND and self.name == Type.DICT \
      or self.base == Type.DICT

  #----------------------------------------------------------------------------
  def is_list(self):
    return self.base == Type.COMPOUND and self.name == Type.LIST \
      or self.base == Type.LIST

  #----------------------------------------------------------------------------
  def is_constant(self):
    return self.base == Type.CONSTANT

  #----------------------------------------------------------------------------
  def is_scalar(self):
    return self.base == Type.SCALAR

  #----------------------------------------------------------------------------
  # todo: why does this not get called??? __setattr__ is called instead. ugh.
  #       hence the reason that it is overridden here... fix!
  #       ugh. solve this `.children` thing...:
  #         a) using generators seems to cause more problems than
  #            it is worth... move .children to return a list.
  #         b) make setting `.children` work.
  @children.setter
  def children(self, value):
    self.setChildren(value)
  def __setattr__(self, key, value):
    if key == 'children':
      return self.setChildren(value)
    return super(Type, self).__setattr__(key, value)
  def setChildren(self, value):
    if not value:
      self.value = None
      return self
    value = list(value)
    if self.base == Type.EXTENSION \
        or ( self.base == Type.COMPOUND and self.name in (Type.LIST, Type.REF) ) \
        or ( self.base in (Type.LIST, Type.REF) ):
      if len(value) > 1:
        raise TypeError('type %r only supports one child' % (self,))
      if len(value) < 1:
        self.value = None
      else:
        self.value = value[0]
      return self
    elif ( self.base == Type.COMPOUND and self.name in (Type.ONEOF, Type.UNION, Type.DICT) )\
        or ( self.base in (Type.ONEOF, Type.UNION, Type.DICT) ):
      self.value = value
    else:
      raise TypeError('type %r does not support children' % (self,))
    return self

  #----------------------------------------------------------------------------
  def __cmp__(self, target):
    if not isinstance(target, self.__class__):
      return cmp(self.__class__, target.__class__)
    for attr in ('base', 'name', 'doc', 'value'):
      cur = cmp(getattr(self, attr), getattr(target, attr))
      if cur != 0:
        return cur
    return 0

  #----------------------------------------------------------------------------
  def tostruct(self, ref=False):
    '''
    Returns a JSONifiable structural representation of this Type.
    Note that all `meta` information is lost.
    '''
    ret = dict(name=self.name)
    if not ref and self.doc:
      ret['doc'] = self.doc
    if self.base == Type.CONSTANT:
      ret['params'] = dict(constant=True, value=self.value)
    elif self.value:
      gen = None
      if self.base == Type.COMPOUND and self.name in (Type.LIST, Type.REF):
        gen = 'item'
      elif self.base == Type.COMPOUND and self.name in (Type.ONEOF, Type.UNION, Type.DICT):
        gen = 'list'
      elif not ref and self.base in (Type.LIST, Type.REF):
        gen = 'item'
      elif not ref and self.base in (Type.ONEOF, Type.UNION, Type.DICT):
        gen = 'list'
      if gen == 'item':
        ret['params'] = dict(value=self.value.tostruct(ref=True))
      elif gen == 'list':
        ret['params'] = dict(value=[v.tostruct(ref=True) for v in self.value])
    if not ref and self.base in (Type.LIST, Type.REF, Type.ONEOF, Type.UNION, Type.DICT):
      ret['base'] = self.base
    return ret

  #----------------------------------------------------------------------------
  def __repr__(self):
    ret = '<Type ' + self.base + ':' + self.name
    if ( self.base == Type.CONSTANT and self.name == Type.NULL ) or \
       ( self.value and \
         ( self.base in (Type.CONSTANT, Type.DICT, Type.EXTENSION) or \
           ( self.base == Type.COMPOUND \
             and self.name in (Type.ONEOF, Type.UNION, Type.LIST, Type.DICT, Type.REF) ) ) ):
      ret += ' value='
      if isinstance(self.value, dict) and not isinstance(self.value, (Type, TypeRef)):
        ret += '{' + ', '.join(
          repr(k) + ': ' + repr(self.value[k])
          for k in sorted(self.value.keys())) + '}'
      else:
        ret += repr(self.value)
    if self.doc:
      ret += ' doc=%r' % (self.doc,)
    return ret + '>'

#------------------------------------------------------------------------------
class TypeRef(_aadict):
  '''
  A `TypeRef` object represents a reference to `Type` object. This
  is typically used within dict-like Types that have named references
  to other Types. A TypeRef can have the following attributes:

  :Attributes:

  type : Type

    The `Type` object being referenced.

  name : str, optional

    The symbolic name attributed to this reference (may be None if
    unnamed).

  doc : str, optional

    Any additional documentation associated with this reference
    instance.

  params : dict, optional

    A lookup table of optional parameters, eg:

    optional : bool
    default : any
  '''

  #----------------------------------------------------------------------------
  def __init__(self, type=None, name=None, doc=None, params=None, *args, **kw):

    # TODO: enable this...
    # if not type:
    #   raise ValueError('TypeRef "type" parameter is required')
    if type:
      kw['type'] = type

    if name:
      kw['name'] = name
    if doc:
      kw['doc'] = doc
    if params:
      kw['params'] = params
    super(TypeRef, self).__init__(*args, **kw)

  #----------------------------------------------------------------------------
  def clone(self):
    params = copy.deepcopy(self.params)
    type   = copy.deepcopy(self.type)
    return TypeRef(type=type, name=self.name, doc=self.doc, params=params)

  #----------------------------------------------------------------------------
  @property
  def children(self):
    if not self.type:
      return
    yield self.type

  #----------------------------------------------------------------------------
  def is_dict(self):         return False
  def is_list(self):         return False
  def is_constant(self):     return False
  def is_scalar(self):       return False

  #----------------------------------------------------------------------------
  def tostruct(self, ref=False):
    ret = dict(type=self.type.tostruct(ref=True))
    if self.params:
      ret['params'] = dict(self.params)
    if self.name:
      ret['name'] = self.name
    if self.doc:
      ret['doc'] = self.doc
    return ret

  #----------------------------------------------------------------------------
  def __cmp__(self, target):
    if not isinstance(target, self.__class__):
      return cmp(self.__class__, target.__class__)
    for attr in ('type', 'name', 'doc', 'params'):
      cur = cmp(getattr(self, attr), getattr(target, attr))
      if cur != 0:
        return cur
    return 0

  #----------------------------------------------------------------------------
  def __repr__(self):
    ret = '<TypeRef '
    if self.name:
      ret += self.name + '='
    ret += repr(self.type)
    if self.params:
      ret += ' params=%r' % (self.params,)
    if self.doc:
      ret += ' doc=%r' % (self.doc,)
    return ret + '>'

#------------------------------------------------------------------------------

whitespace_cre  = re.compile(r'\s+')
hex_cre         = re.compile(r'([a-f0-9][a-f0-9])+', re.IGNORECASE)
constant_cre    = re.compile(r'[0-9"\'-{\\[]')
# todo: move this into TypeRegistry as a configurable option...
#       ==> and make it depend on declared aliases, etc...
symbol_cre      = re.compile(r'[a-z_]([a-z0-9_.]*)?', re.IGNORECASE)

#------------------------------------------------------------------------------
class StringWalker(object):

  #----------------------------------------------------------------------------
  def __init__(self, string, *args, **kw):
    super(StringWalker, self).__init__(*args, **kw)
    self._string  = string
    self.index    = 0

  #----------------------------------------------------------------------------
  @property
  def string(self):
    return self._string[self.index:]

  #----------------------------------------------------------------------------
  @property
  def length(self):
    ret = len(self._string) - self.index
    if ret <= 0:
      return 0
    return ret

  #----------------------------------------------------------------------------
  def __bool__(self):
    return self.length > 0

  #----------------------------------------------------------------------------
  def eatws(self):
    match = whitespace_cre.match(self.string)
    if match:
      self.index += len(match.group(0))
    return self

  #----------------------------------------------------------------------------
  def peek(self, length=1):
    if length <= 0:
      raise ValueError('length must be positive')
    return self.string[:length]

  #----------------------------------------------------------------------------
  def startswith(self, string):
    return self.peek(len(string)) == string

  #----------------------------------------------------------------------------
  def read(self, length=1):
    if length <= 0:
      raise ValueError('length must be positive')
    ret = self.string[:length]
    self.index += length
    return ret

  #----------------------------------------------------------------------------
  def seek(self, position):
    self.index = position
    return self

#------------------------------------------------------------------------------
class TypeRegistry(object):

  DEFAULT_OPTIONS = {
    'extensions'          : None,
    'commentToken'        : '##',
    'closure_open'        : '(',
    'closure_close'       : ')',
    'oneof_sep'           : '|',
    'union_sep'           : '&',
    'customDictTypeRE'    : r'^([a-zA-Z_][a-zA-Z0-9_]*\.)*[A-Z][a-zA-Z0-9_]*$',
    'unknownTypeRE'       : r'^([a-zA-Z_][a-zA-Z0-9_]*\.)*[a-zA-Z0-9_]+$',
  }

  DEFAULT_ALIASES = {
    # constants:
    'null'     : ['nil', 'none', 'None', 'NULL', 'NIL', 'NONE'],
    'true'     : ['True', 'TRUE'],
    'false'    : ['False', 'FALSE'],
    # scalars:
    'byte'     : [],
    'bytes'    : [],
    'boolean'  : ['bool'],
    'integer'  : ['int'],
    'number'   : ['num', 'float', 'decimal', 'real'],
    'string'   : ['str'],
    # meta / compounds types:
    'any'      : [],
    'oneof'    : ['choice', 'enum', 'enumeration', 'select', 'option'],
    'union'    : ['allof'],
    'list'     : ['array', 'vector'],
    'dict'     : ['dictionary', 'hash', 'map', 'hashmap', 'table', 'hashtable'],
    'ref'      : ['reference'],
  }

  #----------------------------------------------------------------------------
  def __init__(self, options=None, aliases=None, _hack=False):
    if _hack:
      return
    self.options    = aadict(self.DEFAULT_OPTIONS).update(options or {})
    self._types     = dict()
    self._autotypes = dict()
    self._aliases   = dict()
    self._dictType_cre    = re.compile(self.options.customDictTypeRE)
    self._unknownType_cre = re.compile(self.options.unknownTypeRE)
    aliases = aliases or self.options.aliases
    self.addAliases(self.DEFAULT_ALIASES if aliases is None else aliases)
    if aliases is None:
      self.addHttpAliases()
    for target, val in morph.pick(self.options, prefix='alias.').items():
      for source in morph.tolist(val):
        self.addAlias(source, target)
    if self.options.extensions:
      self.loadExtensions(self.options.extensions)

  #----------------------------------------------------------------------------
  def clone(self):
    '''
    Creates a copy of this TypeRegistry, where the types are
    deep-copied.
    '''
    ret = TypeRegistry(_hack=True)
    ret.options          = aadict(self.options)
    ret._dictType_cre    = self._dictType_cre
    ret._unknownType_cre = self._unknownType_cre
    ret._aliases         = {k : set(v) for k, v in self._aliases.items()}
    ret._types           = {k : v.clone() for k, v in self._types.items()}
    ret._autotypes       = {k : v.clone() for k, v in self._autotypes.items()}
    return ret

  #----------------------------------------------------------------------------
  def addAliases(self, aliases):
    for target, sources in (aliases or {}).items():
      for source in sources:
        self.addAlias(source, target)

  #----------------------------------------------------------------------------
  def addHttpAliases(self):
    '''
    Loads the HTTP error response codes from pyramid.httpexceptions as
    aliases so that they can be used as output or error response types
    without needing to define them. Several aliases are loaded per
    response code - for example, all of the following will resolve to
    a ``403`` response code:

    * ``HTTPForbidden``
    * ``pyramid.httpexceptions.HTTPForbidden``
    '''
    for name in dir(pyramid.httpexceptions):
      if name.startswith('_'):
        continue
      try:
        sym = getattr(pyramid.httpexceptions, name)
        if inspect.isclass(sym) \
            and issubclass(sym, pyramid.httpexceptions.WSGIHTTPException):
          self.addAlias('pyramid.httpexceptions.' + name, name)
          self.registerAutoType(
            Type(
              base = Type.DICT,
              name = name,
              doc  = _('{error.explanation}', error=sym),
              value = [
                TypeRef(
                  name = 'code',
                  type = Type(base=Type.CONSTANT, name=Type.INTEGER, value=sym.code)),
                TypeRef(
                  name = 'message',
                  type = Type(base=Type.CONSTANT, name=Type.STRING, value=sym.title)),
              ],
              meta = {
                'source'  : 'pyramid.httpexceptions',
                'classes' : ['source-pyramid-httpexceptions'],
              },
            ))
      except Exception:
        pass

  #----------------------------------------------------------------------------
  def addAlias(self, source, target):
    # todo: check for cyclical references...
    if source in self._types or source in self._aliases:
      raise ValueError(
        'cannot alias %r to %r: already declared as standalone type' %
        (source, target))
    for ctarget, csources in self._aliases.items():
      if source in csources and target != ctarget:
        raise ValueError(
          'cannot alias %r to %r: already aliased to %r' %
          (source, target, ctarget))
    if target not in self._aliases:
      self._aliases[target] = set()
    self._aliases[target].add(source)

  #----------------------------------------------------------------------------
  def loadExtensions(self, specs):
    for ext in morph.tolist(specs):
      self.loadExtension(ext)

  #----------------------------------------------------------------------------
  def loadExtension(self, spec):
    log.debug('loading type registry extensions from: %r', spec)
    try:
      sym = asset.symbol(spec)
      return sym(self)
    except (ImportError, AttributeError):
      pass
    try:
      return self.loadExtensionString(asset.load(spec).read(), source=spec)
    except (ImportError, AttributeError, ValueError):
      pass
    return self.loadExtensionString(spec)

  #----------------------------------------------------------------------------
  def loadExtensionString(self, text, source=None):
    from .syntax.numpydoc.parser import Parser
    parser = Parser(comment=self.options.commentToken)
    for doc, typ in parser.parseMulti(text):
      if doc:
        log.debug('ignoring unbound extension documentation text: %r', doc)
      if not typ:
        continue
      if isinstance(typ, TypeRef):
        typ = Type(base=Type.EXTENSION, name=typ.name, doc=typ.doc, value=
          TypeRef(type=typ.type, params=typ.params))
      if source:
        typ.meta.source = source
      log.debug('registering extension type "%s"', typ.name)
      self.registerAutoType(typ)

  #----------------------------------------------------------------------------
  def registerType(self, type):
    if not type.doc and not type.value:
      type = self.getAuto(type.name) or type
    else:
      type = self.dereference(type)
    # todo: should this check for collision?...
    self._types[type.name] = type
    return type

  #----------------------------------------------------------------------------
  def registerAutoType(self, type):
    type = self.dereference(type, auto=True)    
    # todo: should this check for collision?...
    self._autotypes[type.name] = type
    return type

  #----------------------------------------------------------------------------
  def dereference(self, type, auto=False):
    # TODO: in the end, this is just resolving `unknown` types, but
    #       should really do a more "complete" deref. the core problem
    #       is that `pyramid_describe/syntax/numpydoc/merger.py` needs
    #       to "work well" with this... and it currently does not.
    if isinstance(type, TypeRef):
      if type.type:
        type.type = self.dereference(type.type, auto=auto)
      return type
    if type.is_constant() or type.is_scalar():
      return type
    if type.base == Type.UNKNOWN:
      typ = self.getAuto(type.name) if auto else self.get(type.name)
      if not typ:
        raise ValueError(
          'invalid reference to unknown/undefined type "%s"' % (type.name,))
      type = typ
      return type
    type.setChildren(
      self.dereference(typ, auto=auto) for typ in type.children)
    return type

  #----------------------------------------------------------------------------
  def resolveAliases(self, symbol):
    for key, val in self._aliases.items():
      if symbol in val:
        return self.resolveAliases(key)
    return symbol

  #----------------------------------------------------------------------------
  def get(self, symbol):
    symbol = self.resolveAliases(symbol)
    if symbol not in self._types and symbol in self._autotypes:
      # TODO: what about promoting other auto types that are
      #       referenced by self._autotypes[symbol]???
      self._types[symbol] = self._autotypes[symbol]
    return self._types.get(symbol)

  #----------------------------------------------------------------------------
  def getAuto(self, symbol):
    symbol = self.resolveAliases(symbol)
    return self._autotypes.get(symbol)

  #----------------------------------------------------------------------------
  def typeNames(self):
    return sorted(self._types.keys(), key=str.lower)

  #----------------------------------------------------------------------------
  def types(self):
    return sorted(self._types.values(), key=lambda typ: typ.name.lower())

  #----------------------------------------------------------------------------
  def prepareParams(self, type):
    from . import params
    return params.prepare(type.params)

  #----------------------------------------------------------------------------
  # TODO: MOVE THIS INTO pyramid_describe/syntax/numpydoc/parser.py
  #----------------------------------------------------------------------------

  #----------------------------------------------------------------------------
  def parseType(self, spec, complete=True):
    src = StringWalker(spec)
    typ = self._parseType(src)
    if src.string and src.string.startswith(self.options.commentToken):
      src.read(len(src.string))
    if not typ or src.index <= 0:
      raise ValueError('could not parse %r' % (spec,))
    rem = src.string
    if not complete:
      return (typ, rem)
    if not rem:
      return typ
    raise ValueError(
      'Extra data after position %d (%r)' % (src.index, src.string))

  #----------------------------------------------------------------------------
  def _parseType(self, source):
    typ = self._parseType_next(source)
    if not typ:
      return typ
    if not source.eatws():
      return typ
    for seqtyp, seqtok in [
        (Type.ONEOF, self.options.oneof_sep),
        (Type.UNION, self.options.union_sep),
      ]:
      if source.startswith(seqtok):
        return self._parseType_sequence(source, typ, seqtyp, seqtok)
    return typ

  #----------------------------------------------------------------------------
  def _parseType_sequence(self, source, current, base, token):
    while True:
      if not source.eatws():
        return current
      if not source.startswith(token):
        return current
        # raise ValueError(
        #   'cannot parse after %s separator (%r) at position %d (%r)'
        #   % (base, token, source.index, source.string))
      idx = source.index
      source.read(len(token))
      if current.name != base:
        current = Type(base=Type.COMPOUND, name=base, value=[current])
      styp = self._parseType_next(source)
      if not styp:
        source.seek(idx)
        raise ValueError(
          'cannot parse after %s separator (%r) at position %d (%r)'
          % (base, token, source.index, source.string))
      current.value.append(styp)

  #----------------------------------------------------------------------------
  def _peekSymbol(self, source):
    match = symbol_cre.match(source.string)
    if not match:
      return None
    return match.group(0)

  #----------------------------------------------------------------------------
  def _parseType_next(self, source):
    if not source.eatws():
      return None
    if source.startswith(self.options.closure_open):
      idx = source.index
      source.read(1)
      typ = self._parseType(source)
      if not typ:
        source.seek(idx)
        raise ValueError(
          'cannot parse content of grouping (%r) at position %d (%r)' \
            % (self.options.closure_open, source.index, source.string))
      source.eatws()
      if source.read(1) != self.options.closure_close:
        source.seek(idx)
        raise ValueError(
          'unterminated %r at position %d (%r)' \
            % (self.options.closure_open, source.index, source.string))
      return typ
    token = self._peekSymbol(source)
    if token:
      typ = self._parseType_token(source, token)
      if typ:
        return typ
    if constant_cre.match(source.string):
      typ = self._parseType_constant(source)
      if typ:
        return typ
    return None

  #----------------------------------------------------------------------------
  def _parseType_token(self, source, token):
    symbol = self.resolveAliases(token)
    if hasattr(self, '_parseType_symbol_' + symbol):
      typ = getattr(self, '_parseType_symbol_' + symbol)(source, token)
      if typ:
        return typ
    if hasattr(self, '_parseType_compound_' + symbol):
      value = None
      source.read(len(token))
      source.eatws()
      if source.startswith(self.options.closure_open):
        value = self._parseType(source)
      typ = getattr(self, '_parseType_compound_' + token)(source, token, value)
      if typ:
        return typ
    typ = self._parseType_registered(source, token)
    if typ:
      return typ
    typ = self._parseType_custom(source, token)
    if typ:
      return typ
    typ = self._parseType_unknown(source, token)
    if typ:
      return typ
    return None

  #----------------------------------------------------------------------------
  def _makeParseType(**kw):
    def _method(self, source, token):
      source.read(len(token))
      return Type(**kw)
    return _method

  _parseType_symbol_any     = _makeParseType(base=Type.SCALAR,   name=Type.ANY)
  _parseType_symbol_byte    = _makeParseType(base=Type.SCALAR,   name=Type.BYTE)
  _parseType_symbol_bytes   = _makeParseType(base=Type.SCALAR,   name=Type.BYTES)
  _parseType_symbol_boolean = _makeParseType(base=Type.SCALAR,   name=Type.BOOLEAN)
  _parseType_symbol_integer = _makeParseType(base=Type.SCALAR,   name=Type.INTEGER)
  _parseType_symbol_number  = _makeParseType(base=Type.SCALAR,   name=Type.NUMBER)
  _parseType_symbol_string  = _makeParseType(base=Type.SCALAR,   name=Type.STRING)
  _parseType_symbol_null    = _makeParseType(base=Type.CONSTANT, name=Type.NULL,    value=None)
  _parseType_symbol_true    = _makeParseType(base=Type.CONSTANT, name=Type.BOOLEAN, value=True)
  _parseType_symbol_false   = _makeParseType(base=Type.CONSTANT, name=Type.BOOLEAN, value=False)

  # this is a "parseType_symbol" not "parseType_compound" because
  # you can't declare it as "dict(...)"...
  # todo: is this *absolutely* true?...
  _parseType_symbol_dict    = _makeParseType(base=Type.COMPOUND, name=Type.DICT)

  #----------------------------------------------------------------------------
  def _parseType_constant(self, source):
    if source.startswith('0x'):
      return self._parseType_constant_hex(source)
    if source.peek() in '01234567890-':
      return self._parseType_constant_num(source)
    if source.peek() in '\'"{[':
      return self._parseType_constant_yaml(source)
    return None

  #----------------------------------------------------------------------------
  def _parseType_native(self, target):
    if isinstance(target, types.NoneType):
      return Type(base=Type.CONSTANT, name=Type.NULL, value=None)
    if isinstance(target, types.BooleanType):
      return Type(base=Type.CONSTANT, name=Type.BOOLEAN, value=target)
    if isinstance(target, (types.IntType, types.LongType)):
      return Type(base=Type.CONSTANT, name=Type.INTEGER, value=target)
    if isinstance(target, types.FloatType):
      return Type(base=Type.CONSTANT, name=Type.NUMBER, value=target)
    if isinstance(target, six.string_types) \
        or isinstance(target, six.text_type):
      return Type(base=Type.CONSTANT, name=Type.STRING, value=target)
    if isinstance(target, six.binary_type):
      return Type(base=Type.CONSTANT, name=Type.BYTES, value=target)
    if isinstance(target, (types.TupleType, types.ListType)):
      return Type(base=Type.CONSTANT, name=Type.LIST, value=list(target))
    if isinstance(target, types.DictType):
      return Type(base=Type.CONSTANT, name=Type.DICT, value=dict(target))
    raise ValueError('unknown constant type: %r' % (target,))

  #----------------------------------------------------------------------------
  def _parseType_constant_hex(self, source):
    if not source.string.startswith('0x'):
      return None
    match = hex_cre.match(source.string[2:])
    if not match:
      return None
    data = match.group(0)
    source.read(len(data) + 2)
    if len(data) == 2:
      return Type(base=Type.CONSTANT, name=Type.BYTE, value=data.decode('hex'))
    return Type(base=Type.CONSTANT, name=Type.BYTES, value=data.decode('hex'))

  #----------------------------------------------------------------------------
  def _parseType_constant_num(self, source):
    # NOTE: using json, not yaml, because yaml is far too lenient.
    # for example ``78 !foo~`` would be interpreted as the entire
    # *string* "78 !foo~", not the number 78 + plus extra stuff...
    try:
      ret = json.loads(source.string)
      source.read(source.length)
      return self._parseType_native(ret)
    except ValueError as exc:
      if not str(exc).startswith('Extra data: line 1 column '):
        raise
      idx = int(str(exc).split()[5]) - 1
      ret = json.loads(source.string[:idx])
      source.read(idx)
      return self._parseType_native(ret)

  #----------------------------------------------------------------------------
  _yaml_error_cre = re.compile(
    r'^  in "<string>", line 1, column (\d+):$', flags=re.MULTILINE)
  def _parseType_constant_yaml(self, source):
    try:
      ret = yaml.load(source.string)
      source.read(source.length)
      return self._parseType_native(ret)
    except (yaml.parser.ParserError, yaml.parser.ScannerError) as exc:
      idxs = [
        val for val in [
          int(m.group(1)) - 1
          for m in self._yaml_error_cre.finditer(str(exc))]
        if val > 0]
      if not idxs:
        raise
      for idx in reversed(sorted(idxs)):
        try:
          ret = yaml.load(source.string[:idx])
        except Exception as exc:
          continue
        source.read(idx)
        return self._parseType_native(ret)
      raise

  #----------------------------------------------------------------------------
  def _parseType_compound_oneof(self, source, token, value):
    kw = {} if value is None else {'value': value}
    return Type(base=Type.COMPOUND, name=Type.ONEOF, **kw)

  #----------------------------------------------------------------------------
  def _parseType_compound_union(self, source, token, value):
    kw = {} if value is None else {'value': value}
    return Type(base=Type.COMPOUND, name=Type.UNION, **kw)

  #----------------------------------------------------------------------------
  def _parseType_compound_list(self, source, token, value):
    return Type(base=Type.COMPOUND, name=Type.LIST, value=value)

  #----------------------------------------------------------------------------
  def _parseType_compound_ref(self, source, token, value):
    return Type(base=Type.COMPOUND, name=Type.REF, value=value)

  #----------------------------------------------------------------------------
  def _parseType_compound_dict(self, source, token, value):
    for val in value or []:
      if not isinstance(val, TypeRef) or not val.name:
        raise ValueError(
          'dict-type children must be named type references, not %r' % (val,))
    return Type(base=Type.COMPOUND, name=Type.DICT, value=value)

  #----------------------------------------------------------------------------
  def _parseType_registered(self, source, token):
    target = self.resolveAliases(token)
    target = self._types.get(target) or self._autotypes.get(target)
    if not target:
      return None
    source.read(len(token))
    return Type(base=target.base, name=token)

  #----------------------------------------------------------------------------
  def _parseType_custom(self, source, token):
    if not self.isCustomDictType(token):
      return None
    source.read(len(token))
    # todo: how to detect non-dict custom types?...
    #       perhaps simple: NOT the parser's job.
    token = self.resolveAliases(token)
    return Type(base=Type.DICT, name=token)

  #----------------------------------------------------------------------------
  def _parseType_unknown(self, source, token):
    if not self.isUnknownType(token):
      return None
    source.read(len(token))
    # todo: how to detect invalid types?...
    #       perhaps simple: NOT the parser's job.
    token = self.resolveAliases(token)
    return Type(base=Type.UNKNOWN, name=token)

  #----------------------------------------------------------------------------
  def isType(self, name):
    # todo: this is a hack to allow sharing of the regex used to
    #       determine whether or not a symbol is an acceptable
    #       type in pyramid_describe/syntax/numpydoc/extractor.py
    #       fix!
    match = symbol_cre.match(name)
    if match and match.group(0) == name:
      return True
    if self.isCustomDictType(name):
      return True
    return self.isUnknownType(name)

  #----------------------------------------------------------------------------
  def isCustomDictType(self, name):
    return bool(self._dictType_cre.match(name))

  #----------------------------------------------------------------------------
  def isUnknownType(self, name):
    return bool(self._unknownType_cre.match(name))


#------------------------------------------------------------------------------
# end of $Id$
# $ChangeLog$
#------------------------------------------------------------------------------
