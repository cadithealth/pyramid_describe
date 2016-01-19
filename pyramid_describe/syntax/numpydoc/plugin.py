# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2014/05/07
# copy: (C) Copyright 2014-EOT Cadit Inc., All Rights Reserved.
#------------------------------------------------------------------------------

import logging
import asset
from aadict import aadict

from ...typereg import Type, TypeRef
from .extractor import FixedNumpyDocString, decomment
from .parser import Parser
from .merger import resolveTypes, mergeTypes

#----------------------------------------------------------------------------

log = logging.getLogger(__name__)

#------------------------------------------------------------------------------
def _typeFromNumpy(context, nlines):
  # from .extractor import numpy2type
  # return numpy2type(context, nlines)

  if 'numpydoc' not in context:
    context.numpydoc = aadict()
  if 'parser' not in context.numpydoc:
    context.numpydoc.parser = Parser(comment=context.options.commentToken)
  parser = context.numpydoc.parser
  res = list(parser.parseNumpyMulti(nlines, eager=True))
  if not res:
    return None

  # todo: push this logic into `Parser`... there's too much "shared
  #       responsibility and awareness"... ugh.

  if len(res) > 1:
    types = [typ.__class__.__name__
             for typ in filter(None, [item[1] for item in res])]
    if len(set(types)) > 1:
      raise ValueError(
        'context does not support mixing types and attributes: %r'
        % (nlines,))

  doc = None
  typ = None
  for idx, item in enumerate(res):
    sub = item[1]

    # todo: this is a big time hack. basically, a dict-like Type
    #       definition *WITHOUT* any attributes is resampled to be a
    #       dangling TypeRef with documentation... this is then
    #       de-referenced during the merge phase... ugh.
    if sub and sub.base == Type.DICT and sub.doc and not sub.value:
      sub = TypeRef(doc=sub.doc, type=Type(base=sub.base, name=sub.name))
    # /todo

    if idx == 0:
      doc = item[0]
      typ = sub
      if sub:
        if isinstance(typ, TypeRef) and typ.name:
          typ = Type(base=Type.COMPOUND, name=Type.DICT, value=[typ])
        else:
          typ = Type(base=Type.COMPOUND, name=Type.ONEOF, value=[typ])
    else:
      if item[0]:
        raise ValueError(
          'context does not support interleaved text: %r' % (item[0],))
      if not sub:
        raise ValueError(
          'unexpected multi-parse returned no type at index %r' % (idx,))
      if isinstance(sub, TypeRef) and sub.name:
        if typ.base != Type.COMPOUND or typ.name != Type.DICT:
          raise ValueError(
            'expected attribute specification, received: %r' % (sub,))
      else:
        if typ.base != Type.COMPOUND or typ.name != Type.ONEOF:
          raise ValueError(
            'expected declared type, received: %r' % (sub,))

      typ.value.append(sub)

  if typ and typ.base == Type.COMPOUND and typ.name == Type.ONEOF \
      and len(typ.value) == 1:
    typ = typ.value[0]

  # /todo

  return (doc or None, typ)

#------------------------------------------------------------------------------
def _spliceTypeFromNumpy(ndoc, entry, context, section):
  res = _typeFromNumpy(context, ndoc[section])
  if not res:
    return None
  ndoc[section] = res[0]
  return res[1]

#------------------------------------------------------------------------------
def _spliceType(ndoc, entry, context, channel):
  # todo: i18n... but does numpydoc even support that???
  section = {
    'input'  : 'Parameters',
    'output' : 'Returns',
    'error'  : 'Raises',
  }[channel]

  try:
    typ = _spliceTypeFromNumpy(ndoc, entry, context, section)

    # if typ and typ.name == 'dict' and len(typ.value) >= 4 \
    #     and typ.value[3].name == 'area':
    #   print 'AREA:',repr(typ.value[3])
    #   print 'LIST:',repr(typ.value[3].type)
    #   print '>'*70
    #   print 'SHAPE:',repr(typ.value[3].type.value)
    #   print '<'*70

    return resolveTypes(entry, context, channel, typ)

  except Exception as err:
    msg = 'failed extracting types from "%s" channel of "%s"' % (
      channel, entry.dpath)
    log.exception(msg)
    raise ValueError(msg + ': ' + str(err))

#------------------------------------------------------------------------------
@asset.plugin('pyramid_describe.plugins.entry.parsers', 'numpydoc', after='title')
def entry_parser(entry, context):
  '''
  This pyramid-describe entry parser plugin extracts NumpyDoc
  documentation about parameters, return values, and exceptions
  into structured information.
  '''
  if not entry or not entry.doc:
    return entry

  ndoc = FixedNumpyDocString(entry.doc)

  # todo: rename these entry attributes to `input`, `output`, and `error`
  entry.params  = _spliceType(ndoc, entry, context, 'input')
  entry.returns = _spliceType(ndoc, entry, context, 'output')
  entry.raises  = _spliceType(ndoc, entry, context, 'error')

  # todo: anything to do with 'Other Parameters', 'Warns', 'Attributes', 'Methods' ?...

  # this re-assembles everything that was not consumed
  entry.doc = decomment(str(ndoc), context.options.commentToken)

  return entry

#------------------------------------------------------------------------------
@asset.plugin('pyramid_describe.plugins.catalog.parsers', 'numpydoc')
def catalog_parser(catalog, context):
  mergeTypes(catalog, context)
  return catalog

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
