# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2015/12/27
# copy: (C) Copyright 2015-EOT Cadit Inc., All Rights Reserved.
#------------------------------------------------------------------------------

import logging
import inspect

from aadict import aadict
import pyramid.httpexceptions

from ...typereg import Type, TypeRef
from ...params import ACCESS_C, ACCESS_R, ACCESS_W, ACCESS_ALL

#------------------------------------------------------------------------------

log = logging.getLogger(__name__)

CHANNEL_ALL             = 'all'

#------------------------------------------------------------------------------
class MergeError(Exception): pass

#------------------------------------------------------------------------------
def resolveTypes(entry, context, channel, typ):
  '''
  Resolves the unbound type definition `typ` into the current context
  state. The `channel` defines how the type is being defined and can
  be one of:

  * ``'input'`` : it describes an input parameter
  * ``'output'`` : it describes an output parameter
  * ``'error'`` : it describes an exception state
  * ``None`` : it is being described out-of-band, i.e. it
    is an "objective" non-parameter description of the object
    type.

  The `context` object may be extended to have the `numpydoc`
  attribute, which will be used during the `catalog.parsers` phase to
  merge all type declarations.
  '''
  if channel not in ('input', 'output', 'error', None):
    raise ValueError('invalid type channel: %r' % (channel,))
  if not typ:
    return typ

  if 'numpydoc' not in context:
    context.numpydoc = aadict()
  if 'types' not in context.numpydoc:
    context.numpydoc.types = dict()

  if channel is None:
    mode = CHANNEL_ALL
  elif channel == 'input':
    if entry.isMethod:
      mode = {
        'POST' : ACCESS_C,
        'GET'  : ACCESS_R,     # todo: input to a GET... hm... what to do!?
        'PUT'  : ACCESS_W,
      }.get(entry.method, CHANNEL_ALL)
    else:
      mode = CHANNEL_ALL
  else:
    mode = ACCESS_R

  def _register(typ, ref):
    if typ.name not in context.numpydoc.types:
      context.numpydoc.types[typ.name] = {}
    if mode not in context.numpydoc.types[typ.name]:
      context.numpydoc.types[typ.name][mode] = []
    refonly = not ( typ.doc or typ.value )
    context.numpydoc.types[typ.name][mode].append(
      aadict(type=typ, ref=ref, refonly=refonly, mode=mode, entry=entry))

  def _walk(typ):
    ref = typ
    if isinstance(typ, TypeRef):
      typ = typ.type
    else:
      if typ.base == Type.DICT:
        ref = TypeRef(type=typ)

    # todo: this is a wholly unsatisfactory implementation...
    #       - should it genericize aliasing to all types?
    #       - perhaps resolution should be done during parsing on-the-fly?

    if typ.base == Type.DICT:
      typ.name = context.options.typereg.resolveAliases(typ.name)
      _register(typ, ref)
      if typ.value:
        typ.value = [_walk(t) for t in typ.value]
    elif typ.base == Type.COMPOUND and typ.name in (Type.ONEOF, Type.UNION, Type.DICT):
      if typ.value:
        typ.value = [_walk(t) for t in typ.value]
    elif typ.base == Type.COMPOUND and typ.name in (Type.LIST, Type.REF):
      if typ.value:
        typ.value = _walk(typ.value)
    elif typ.base == Type.UNKNOWN:
      ref.type = context.options.typereg.get(typ.name)
      if not ref.type:
        raise ValueError(
          'invalid reference to unknown/undefined type "%s"' % (typ.name,))
    return ref

  return _walk(typ)

#------------------------------------------------------------------------------
def mergeTypes(catalog, context):
  types = context.get('numpydoc', {}).get('types', {})
  for name, decls in types.items():
    try:
      typ = _mergeType(context, name, decls)
    except Exception as err:
      # todo: actualy filename may be more useful...
      sources = [reg.entry.dpath
                 for lst in decls.values()
                 for reg in lst
                 if not reg.refonly]
      errstr = 'error merging type "%s" (declared in "%s")' \
        % (name, '", "'.join(sources))
      log.exception(errstr)
      raise MergeError(errstr + ': ' + str(err))
    catalog.typereg.registerType(typ)
  _dereferenceCatalog(catalog)
  # release the cache!
  types.clear()

#------------------------------------------------------------------------------
def _mergeType(context, typname, regset):
  bases = list(set([reg.type.base for regs in regset.values() for reg in regs]))
  if len(bases) != 1:
    raise ValueError('conflicting base types: %r' % (bases,))
  if bases[0] == Type.DICT:
    return _mergeDict(context, typname, regset)
  raise NotImplementedError('unexpected base type: %r' % (bases[0],))

#------------------------------------------------------------------------------
def _mergeDict(context, typname, regset):
  allregs = [reg for regs in regset.values() for reg in regs]
  ret = Type(base=Type.DICT, name=allregs[0].type.name)

  # merge the documentation
  ret.doc = _mergeDocs(context, allregs)
  for reg in allregs:
    reg.type.doc = None

  # merge access channels separately
  normspecs = {}
  for mode in ACCESS_ALL + [CHANNEL_ALL]:
    if mode in regset:
      for reg in regset[mode]:
        normspecs[mode] = _mergeDictSameMode(
          context, typname, normspecs.get(mode), reg.type)

  # if a channel does not specify *any* attributes, it is ignored
  # (the assumption is that it is a simple reference with optional
  # documentation).
  # TODO: promote any docs to the referencing TypeRef!...
  normspecs = {mode: spec for mode, spec in normspecs.items() if spec.value}

  curtyps = filter(None, normspecs.values())
  if len(curtyps) == 1:
    # special casing single-declarations so that *no* access mode
    # adjustments are made
    ret.value = curtyps[0].value
    return ret

  attrnames = sorted(set([
    val.name
    for spec in normspecs.values()
    for val in spec.value]))

  attributes = []
  for attrname in attrnames:
    attrs = {mode: attr
             for mode, spec in normspecs.items()
             for attr in spec.value
             if attr.name == attrname}
    newattr = TypeRef(type=attrs.values()[0].type, name=attrname)
    for attr in attrs.values():
      if attr.doc:
        if newattr.doc and newattr.doc != attr.doc:
          raise ValueError(
            'attribute "%s" documentation collision' % (attrname,))
        newattr.doc = attr.doc
    params = {}
    for mode, attr in attrs.items():
      if not attr.params:
        continue
      for key, val in attr.params.items():
        if key in params and params[key] != val:
          raise ValueError(
            'attribute "%s" option "%s" collision' % (attrname, key))
        params[key] = val

    # if NONE of the access control params are set AND the attribute
    # is not specified in ALL defined channels (or the ALL channel),
    # then add access parameters based on channel. also "write"
    # implies "create", and "create" where there is no "write" channel
    # definition implies "write".
    if not set(params.keys()) & set(ACCESS_ALL):
      modes = attrs.keys()
      if ACCESS_W in modes and ACCESS_C not in modes:
        modes.append(ACCESS_C)
      if ACCESS_C in modes and ACCESS_W not in modes \
          and ACCESS_W not in normspecs.keys():
        modes.append(ACCESS_W)
      if CHANNEL_ALL not in modes \
          and set(modes) & set(ACCESS_ALL) != set(ACCESS_ALL):
        params.update({mode: True for mode in modes})
    if params:
      newattr.params = params
    attributes.append(newattr)

  if attributes:
    ret.value = attributes
  return ret

#------------------------------------------------------------------------------
def _findCommonDoc(t1, t2):
  if t1 in t2:
    return t1
  if t2 in t1:
    return t2
  # todo: this is a pretty primitive shared-tail text comparison...
  #       at the very least, it should rst-normalize the texts first.
  t1 = list(reversed(t1.split('\n')))
  t2 = list(reversed(t2.split('\n')))
  idx = 0
  while True:
    if idx >= len(t1) or idx >= len(t2):
      break
    if t1[idx] != t2[idx]:
      break
    idx += 1
  if idx <= 0:
    return ''
  return '\n'.join(reversed(t1[:idx])).strip()

#------------------------------------------------------------------------------
def _moveCommonDoc(parent, current, common):
  if not common:
    if parent and parent.strip():
      return parent + '\n\n' + current
    return current
  current = current.strip()
  common  = common.strip()
  if not current.endswith(common):
    raise ValueError(
      'internal error -- unexpected non-intersection of common text: %r'
      % (common,))
  return _moveCommonDoc(parent, current[: - len(common)].strip(), None)

#------------------------------------------------------------------------------
def _mergeDocs(context, regs):
  # TODO: there is a *ton* of gratuitous ``.strip()`` going on as a
  #       product of this function... elliminate somehow!
  regs = [reg for reg in regs if reg.type.doc]
  if not regs:
    return None
  if len(regs) == 1:
    return regs[0].type.doc
  common = reduce(_findCommonDoc, [reg.type.doc for reg in regs])
  for reg in regs:
    reg.ref.doc = _moveCommonDoc(reg.ref.doc, reg.type.doc, common)
  return common

#------------------------------------------------------------------------------
def _mergeDictSameMode(context, typname, typA, typB):
  if typA is None or typB is None:
    return typA or typB or None
  if typA == typB:
    return typA
  return Type(
    base=typA.base, name=typA.name, value=_mergeDictValue(typA.value, typB.value))

#------------------------------------------------------------------------------
def _mergeDictValue(valA, valB):
  if not valA:
    return valB
  if not valB:
    return valA
  valA = {ref.name: ref for ref in valA}
  valB = {ref.name: ref for ref in valB}
  attrnames = sorted(set(valA.keys() + valB.keys()))
  ret = []
  for attrname in attrnames:
    attrA = valA.get(attrname)
    attrB = valB.get(attrname)
    if not attrA or not attrB or attrA == attrB:
      ret.append(attrA or attrB)
      continue
    if attrA.type != attrB.type:
      raise ValueError(
        'conflicting declaration of attribute "%s" type: %r != %r'
        % (attrname, attrA.type, attrB.type))
    if attrA.params != attrB.params:
      raise ValueError(
        'conflicting declaration of attribute "%s" parameters: %r != %r'
        % (attrname, attrA.params, attrB.params))
    if attrA.doc != attrB.doc:
      raise ValueError(
        'conflicting declaration of attribute "%s" documentation: %r != %r'
        % (attrname, attrA.doc, attrB.doc))
    raise NotImplementedError(
      'unexpected/unknown conflicting definitions of attribute "%s" (%r != %r)'
      % (attrname, attrA, attrB))
  return ret

#------------------------------------------------------------------------------
def _dereferenceCatalog(catalog):
  for endpoint in catalog.endpoints or []:
    _dereferenceEntry(catalog.typereg, endpoint)
    for method in endpoint.methods or []:
      _dereferenceEntry(catalog.typereg, method)

#------------------------------------------------------------------------------
def _dereferenceEntry(typereg, entry):
  for channel in ('params', 'returns', 'raises'):
    typ = getattr(entry, channel, None)
    if typ:
      setattr(entry, channel, _dereferenceType(typereg, typ))

#------------------------------------------------------------------------------
def _dereferenceType(typereg, typ):
  if isinstance(typ, TypeRef):
    typ.type = _dereferenceType(typereg, typ.type)
    if not typ.doc and not typ.name and not typ.params:
      return typ.type
    return typ
  if typ.base == Type.DICT:
    typ = typereg.get(typ.name) or typ
    if typ.value:
      typ.value = [_dereferenceType(typereg, attr) for attr in typ.value]
    return typ
  elif typ.base == Type.EXTENSION:
    typ = typereg.get(typ.name) or typ
    if typ.value:
      typ.value = _dereferenceType(typereg, typ.value)
    return typ
  elif typ.base == Type.COMPOUND and typ.name in (Type.ONEOF, Type.UNION, Type.DICT):
    if typ.value:
      typ.value = [_dereferenceType(typereg, t) for t in typ.value]
  elif typ.base == Type.COMPOUND and typ.name in (Type.LIST, Type.REF):
    if typ.value:
      typ.value = _dereferenceType(typereg, typ.value)
  return typ

#------------------------------------------------------------------------------
# end of $Id$
# $ChangeLog$
#------------------------------------------------------------------------------
