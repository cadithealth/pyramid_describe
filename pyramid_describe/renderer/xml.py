# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2016/01/03
# copy: (C) Copyright 2016-EOT Cadit Inc., All Rights Reserved.
#------------------------------------------------------------------------------

from __future__ import absolute_import

import re
import collections
import xml.etree.ElementTree as ET

import six
import asset

#------------------------------------------------------------------------------
def ccc(name):
  'Convert Camel Case (converts camelCase to camel-case).'
  def repl(match):
    return match.group(1) + '-' + match.group(2).lower()
  return re.sub('([a-z])([A-Z])', repl, name)

#------------------------------------------------------------------------------
def singular(name):
  # todo: ugh.
  if name.endswith('s'):
    return name[:-1]
  return name

#------------------------------------------------------------------------------
def isscalar(obj):
  return isinstance(obj, six.string_types + (bool, int, float))

#------------------------------------------------------------------------------
def islist(obj):
  if isscalar(obj) or isinstance(obj, dict):
    return False
  try:
    list(obj)
    return True
  except TypeError:
    return False

#------------------------------------------------------------------------------
def add2node(obj, node, dashify=True):
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
        if isinstance(v, bool):
          v = str(v).lower()
        node.set(ccc(k) if dashify else k, str(v))
        continue
      if islist(v):
        k = singular(k)
        for el in v:
          node.append(dict2node(dict([(k,el)]), dashify=dashify))
        continue
      node.append(dict2node(dict([(k,v)]), dashify=dashify))
    return
  raise NotImplementedError()

#------------------------------------------------------------------------------
def dict2node(d, dashify=True):
  if len(d) != 1:
    node = ET.Element('element')
    for k, v in d.items():
      node.append(dict2node(dict([(k, v)]), dashify=dashify))
    return node
  node = ET.Element(ccc(d.keys()[0]) if dashify else d.keys()[0])
  add2node(d.values()[0], node, dashify=dashify)
  return node

#------------------------------------------------------------------------------
def et2str(data):
  return ET.tostring(data, 'UTF-8').replace(
    '<?xml version=\'1.0\' encoding=\'UTF-8\'?>',
    '<?xml version="1.0" encoding="UTF-8"?>')

#------------------------------------------------------------------------------
def doc2list(node):
  # force 'doc' attribute into a list, which causes dict2node to
  # make it into a node instead of an attribute
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

#------------------------------------------------------------------------------
@asset.plugin('pyramid_describe.plugins.renderers', 'xml')
def render(catalog):
  data = catalog.describer.structure_render(catalog, dict=collections.OrderedDict)
  doc2list(data)
  return et2str(dict2node(data))


#------------------------------------------------------------------------------
# end of $Id$
# $ChangeLog$
#------------------------------------------------------------------------------
