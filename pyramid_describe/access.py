# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2016/01/12
# copy: (C) Copyright 2016-EOT Cadit Inc., All Rights Reserved.
#------------------------------------------------------------------------------

'''
This module provides a set of pyramid-describe plugins that manage
restricting access to endpoints, types, and documentation based an
access control policies.
'''

import logging

from aadict import aadict
import asset
import morph

# todo: really use a "private" function?...
from .syntax.docorator import _docorator2classes
from .typereg import Type, TypeRef

#------------------------------------------------------------------------------

log = logging.getLogger(__name__)

DEFAULT_ACCESS_PUBLIC   = 'public'
GLOBAL_ACCESS           = '*'

#------------------------------------------------------------------------------
@asset.plugin('pyramid_describe.plugins.entry.filters', 'access')
def entry_filter(entry, context):
  options = _getOptions(context)
  return _entry_filter(entry, context, options)

#------------------------------------------------------------------------------
def _entry_filter(entry, context, options):
  if not entry.doc \
      and not _hasUnion(entry.classes, options.classes) \
      and entry.methods:
    # note: the logic here is that, given that methods are filtered
    #       first, if at least one endpoint's methods passed, and
    #       this endpoint has *NO* documentation (i.e. no docorators),
    #       then grant access to this endpoint.
    classes = []
    for kls in options.rank.classes:
      for method in entry.methods:
        if kls in method.classes:
          classes = [kls]
          break
      if classes:
        break
    entry.classes = list(entry.classes or []) + classes
    classes = classes or options.default.endpoint.classes
  else:
    classes = entry.classes or options.default.endpoint.classes
    if not _hasUnion(classes, options.request.classes):
      return None
  entry.params  = _type_filter(entry.params,  context, options, inherit_classes=classes)
  entry.returns = _type_filter(entry.returns, context, options, inherit_classes=classes)
  entry.raises  = _type_filter(entry.raises,  context, options, inherit_classes=classes)
  entry.doc     = _text_filter(entry.doc,     context, options)
  return entry

#------------------------------------------------------------------------------
@asset.plugin('pyramid_describe.plugins.entry.filters', 'access')
def type_filter(type, context):
  options = _getOptions(context)
  return _type_filter(type, context, options)

#------------------------------------------------------------------------------
def _type_filter(type, context, options, inherit_classes=None):
  if not type:
    return type

  # todo: this feels *slightly* hackish... generalize somehow?
  #       ==> the generalized solution should prolly also cover
  #           primitives, eg 'integer', etc.
  if type.get('meta', {}).get('source') == 'pyramid.httpexceptions':
    return type

  default_classes = options.default.type.classes
  if isinstance(type, Type):
    classes = type.meta.classes
  elif isinstance(type, TypeRef):
    classes = (type.params or {}).get('classes', None)
    if type.name:
      default_classes = options.default.attribute.classes
  else:
    raise ValueError('unknown type: %r' % (type,))

  if not _hasUnion(
      classes or inherit_classes or default_classes,
      options.request.classes):
    return None

  if isinstance(type, Type):
    children = list(type.children)
    if children:
      filtered = []
      for child in children:
        if isinstance(child, Type) and context.catalog.typereg.get(child.name):
          filtered.append(child)
        else:
          filtered.append(
            _type_filter(child, context, options, inherit_classes=inherit_classes))
      type.setChildren(filter(None, filtered))
  elif isinstance(type, TypeRef):
    sub_classes = classes or inherit_classes or default_classes
    type.type = _type_filter(
      type.type, context, options, inherit_classes=sub_classes)
    if not type.type:
      return None
  else:
    raise ValueError('unknown type: %r' % (type,))

  type.doc = _text_filter(type.doc, context, options)

  return type

#------------------------------------------------------------------------------
def _text_filter(text, context, options):
  if not text:
    return text
  return text
  from .doctree import rst2document, document2rst
  from docutils import nodes
  rdoc = rst2document(text)
  def _selectNode(node):
    attrs = getattr(node, 'attributes', None)
    if not attrs:
      return True
    classes = attrs.get('classes', None)
    if not classes:
      return True
    if not _hasUnion(classes, options.classes):
      return True
    return _hasUnion(classes, options.request.classes)
  def _filterTree(node):
    if not node or not isinstance(node, nodes.Node):
      return node
    if not _selectNode(node):
      return None
    children = getattr(node, 'children', None)
    if not children:
      return node
    node.children = filter(None, [_filterTree(sub) for sub in children])
    return node
  rdoc = _filterTree(rdoc)
  return document2rst(rdoc)

#------------------------------------------------------------------------------
@asset.plugin('pyramid_describe.plugins.entry.filters', 'access')
def catalog_filter(catalog, context):
  # note: there really is nothing to do here, but this provides a
  #       nice central place to issue a single warning about not
  #       doing any access control...
  # todo: perhaps do this even more centrally, so that it the
  #       warning gets emitted only once per program lifetime?
  options = _getOptions(context)
  if options.control is _defaultAccessControl:
    log.warning(
      'pyramid_describe "access.control" setting is not set...'
      + ' defaulting to allowing "public" access only')
  return catalog

#------------------------------------------------------------------------------
def _hasUnion(setA, setB):
  if not setA or not setB:
    return False
  for item in setA:
    if item in setB:
      return True
  return False

#------------------------------------------------------------------------------
def _defaultAccessControl(request, *args, **kw):
  return [DEFAULT_ACCESS_PUBLIC]

#------------------------------------------------------------------------------
def _getOptions(context):
  if __name__ in context:
    return context[__name__]
  options = aadict.d2ar(morph.pick(context.options, prefix='access.'))
  # `options.groups` = all known groups LUT
  options.groups = {
    k : aadict({'docorator': v, 'class': list(_docorator2classes(v))[0]})
    for k, v in morph.pick(options, prefix='group.').items()
  }
  # `options.default` = default access for endpoint, type, and attribute
  options.default = aadict({
    node : morph.tolist(options.get('default.' + node))
    for node in ('endpoint', 'type', 'attribute')
  })
  # `options.rank.groups` = ordered list of group ranking (most-public to least-public)
  options.rank = aadict(groups=morph.tolist(options.rank))
  # `options.rank.classes` = ordered list of class ranking
  options.rank.classes = [options.groups[grp]['class'] for grp in options.rank.groups]
  # `options.rank.docorators` = ordered list of docorator ranking
  options.rank.docorators = [options.groups[grp]['docorator'] for grp in options.rank.groups]
  # `options.default[NODE].(groups|classes|docorators)`
  for node, groups in list(options.default.items()):
    options.default[node] = aadict(
      groups     = groups,
      classes    = [options.groups[grp]['class'] for grp in groups],
      docorators = [options.groups[grp]['docorator'] for grp in groups],
    )
  # `options.classes` = all known access classes
  options.classes = [
    group['class'] for group in options.groups.values()]
  # `options.docorators` = all known access docorators
  options.docorators = [
    group['docorator'] for group in options.groups.values()]
  # `options.request` = current request information
  options.request = aadict()
  # `options.control` = request-to-group-access callback
  if not options.control:
    options.control = _defaultAccessControl
  if options.control == GLOBAL_ACCESS:
    options.request.groups = options.groups.keys()
  else:
    options.control = asset.symbol(options.control)
    options.request.groups = options.control(context.request, context=context)
  # `options.request.classes` = the classes this request has access to
  options.request.classes = [
    options.groups[group]['class']
    for group in options.request.groups
    if group in options.groups
  ]
  # `options.request.docorators` = the docorators this request has access to
  options.request.docorators = [
    options.groups[group]['docorator']
    for group in options.request.groups
    if group in options.groups
  ]
  context[__name__] = options
  return options

#------------------------------------------------------------------------------
# end of $Id$
# $ChangeLog$
#------------------------------------------------------------------------------
