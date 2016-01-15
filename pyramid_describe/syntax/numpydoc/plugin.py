# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2014/05/07
# copy: (C) Copyright 2014-EOT Cadit Inc., All Rights Reserved.
#------------------------------------------------------------------------------

import asset

from .extractor import FixedNumpyDocString, numpy2type, decomment
from .merger import registerTypes, mergeTypes

#------------------------------------------------------------------------------
def _spliceTypeFromNumpy(ndoc, entry, context, section):
  res = numpy2type(context, ndoc[section])
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
  typ = _spliceTypeFromNumpy(ndoc, entry, context, section)

  # if typ and typ.name == 'dict' and len(typ.value) >= 4 \
  #     and typ.value[3].name == 'area':
  #   print 'AREA:',repr(typ.value[3])
  #   print 'LIST:',repr(typ.value[3].type)
  #   print '>'*70
  #   print 'SHAPE:',repr(typ.value[3].type.value)
  #   print '<'*70

  # import pdb;pdb.set_trace()

  return registerTypes(entry, context, channel, typ)

#------------------------------------------------------------------------------
@asset.plugin('pyramid_describe.plugins.entry.parsers', 'numpydoc', after='title')
def parser(entry, context):
  '''
  This pyramid-describe entry parser plugin extracts NumpyDoc
  documentation about parameters, return values, and exceptions
  into structured information.
  '''
  if not entry or not entry.doc:
    return entry

  # todo: this really shouldn't be done "globally" like this... i.e.
  #       context-sensitivity may be interesting. for example, the
  #       following numpydoc would be unexpectedly invalid:
  #         Returns:
  #         --------
  #         value : ( number | "some ## weird ## string" )
  entry.doc = decomment(entry.doc, context.options.commentToken)

  ndoc = FixedNumpyDocString(entry.doc)

  # todo: rename these entry attributes to `input`, `output`, and `error`
  entry.params  = _spliceType(ndoc, entry, context, 'input')
  entry.returns = _spliceType(ndoc, entry, context, 'output')
  entry.raises  = _spliceType(ndoc, entry, context, 'error')
  # todo: anything to do with 'Other Parameters', 'Warns', 'Attributes', 'Methods' ?...

  # this re-assembles everything that was not consumed
  entry.doc = str(ndoc)

  return entry

#------------------------------------------------------------------------------
@asset.plugin('pyramid_describe.plugins.catalog.parsers', 'numpydoc')
def catalog_parser(catalog, context):
  mergeTypes(catalog, context)
  return catalog

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
