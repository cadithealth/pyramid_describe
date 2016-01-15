# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2016/01/03
# copy: (C) Copyright 2016-EOT Cadit Inc., All Rights Reserved.
#------------------------------------------------------------------------------

# TODO:
#   this is a really *poor* implementation. i really need to read the spec,
#   *understand* it, and generate something more appropriate...

# sources:
#   http://www.w3.org/Submission/wadl/
#   https://github.com/mnot/wadl_stylesheets/commit/679bc3df66f3cddf73d5e394e2fa28306dccfc77
#   http://webservices.amazon.com/AWSECommerceService/AWSECommerceService.xsd
#   https://wadl.java.net/

from __future__ import absolute_import

import uuid
import collections
import xml.etree.ElementTree as ET

from aadict import aadict
import asset

from ..util import tag
from ..typereg import Type, TypeRef
from .xml import doc2list, et2str, dict2node, isscalar

#------------------------------------------------------------------------------

wadl_type_map = {
  Type.BOOLEAN  : 'xsd:boolean',
  Type.INTEGER  : 'xsd:integer',
  Type.NUMBER   : 'xsd:float',
  Type.STRING   : 'xsd:string',
}

wadl_xmlns = {
  'wadl'        : 'http://wadl.dev.java.net/2009/02',
  'xsd'         : 'http://www.w3.org/2001/XMLSchema',
  'xsi'         : 'http://www.w3.org/2001/XMLSchema-instance',
  'doc'         : 'http://pythonhosted.org/pyramid_describer/xmlns/0.1/doc',
}

#------------------------------------------------------------------------------
def et2entry(catalog, node):
  for attr in ('id', 'decoratedName', 'decoratedPath'):
    node.pop(attr, None)
  if 'params' in node:
    cur = dict()
    mergeNode(cur, struct2schema(node.pop('params')))
    node['request'] = dict(representation=cur)
  if 'returns' in node:
    cur = dict()
    mergeNode(cur, struct2schema(node.pop('returns')))
    node['response'] = dict(representation=cur, status=200)
  if 'raises' in node:
    if 'response' in node:
      node['response'] = [node['response']]
    else:
      node['response'] = []
    raises = node.pop('raises')
    if raises.get('name') == Type.ONEOF and raises.get('params') \
        and raises['params'].get('value'):
      for item in raises['params']['value']:
        cur  = dict()
        mergeNode(cur, struct2schema(item))
        code = 400
        typ  = None
        if item.get('type') and item['type'].get('name'):
          typ = catalog.typereg.get(item['type']['name'])
        if typ and typ.base == Type.DICT and typ.value:
          for attr in typ.value:
            if attr.name == 'code' \
                and attr.type.base == Type.CONSTANT \
                and attr.type.name == Type.INTEGER:
              code = attr.type.value
              break
        node['response'].append(dict(representation=cur, status=code))
    else:
      cur = dict()
      mergeNode(cur, struct2schema(raises))
      node['response'].append(representation=cur, status=400)

#------------------------------------------------------------------------------
def mergeNode(node, value):
  for key, val in value.items():
    if key not in node:
      node[key] = []
    node[key].append(val)

#------------------------------------------------------------------------------
@asset.plugin('pyramid_describe.plugins.renderers', 'wadl')
def render(catalog):
  data = catalog.describer.structure_render(catalog, dict=collections.OrderedDict)
  # force all endpoints to have at least a 'GET' method
  # and strip unwanted attributes from entries
  # TODO: should this be moved into the global describer???
  for endpoint in data['application']['endpoints']:
    et2entry(catalog, endpoint)
    for method in endpoint.get('methods', []):
      et2entry(catalog, method)
    if not endpoint.get('methods'):
      endpoint['methods'] = [dict(name='GET')]
  if data['application']['types']:
    data['application'].pop('types', None)
    data['application']['grammars'] = {
      'xsd:schema' : {
        'targetNamespace'       : data['application'].get('url', None),
        # note: this `app:targetNamespace` is just to force ElementTree
        # to add the `app` namespace declaration.
        'app:targetNamespace'   : data['application'].get('url', None),
        'elementFormDefault'    : 'qualified',
      }
    }
    for name in catalog.typereg.typeNames():
      mergeNode(
        data['application']['grammars']['xsd:schema'],
        struct2schema(catalog.typereg.get(name).tostruct(ref=False), ref=False))

  # force 'doc' attribute into a list, which causes dict2node to
  # make it into a node instead of an attribute
  doc2list(data)

  data = dict2node(data, dashify=False)
  data = et2wadl(catalog.options, data)
  return et2str(data)

#------------------------------------------------------------------------------
def _struct2ref(typ):
  if typ.name in wadl_type_map:
    return wadl_type_map[typ.name]
  return 'app:' + typ.name

#------------------------------------------------------------------------------
def struct2schema(typ, ref=True):
  return _struct2schema(aadict.d2ar(typ), ref=ref)
def _struct2schema(typ, ref=True):

  if typ.type:
    # it's a reference type
    if typ.name:
      ret = dict(
        name      = typ.name,
        minOccurs = 1 if not typ.params or not typ.params.optional else 0,
        maxOccurs = 1,
      )
      if typ.doc:
        ret['doc'] = typ.doc
      mergeNode(ret, _struct2schema(typ.type))
      return {'xsd:element': ret}

    # TODO: ugh. this is not actually representable in XML... shite.
    #       why do people still use XML again?
    ret = dict(ref=_struct2ref(typ.type))
    if typ.doc:
      ret['doc'] = typ.doc
    return {'xsd:element': ret}

  if typ.base == 'dict':
    if ref:
      ret = dict(ref=_struct2ref(typ))
      if typ.doc:
        ret['doc'] = typ.doc
      return {'xsd:element': ret}
    ret = dict(name=typ.name)
    if typ.doc:
      ret['doc'] = typ.doc
    if typ.params and typ.params.value:
      for sub in typ.params.value:
        mergeNode(ret, _struct2schema(sub))
    return {'xsd:complexType': ret}

  if typ.name in wadl_type_map:
    ret = dict(base=wadl_type_map[typ.name])
    if typ.params and typ.params.constant:
      ret['xsd:enumeration'] = dict(value=typ.params.value)
    return {'xsd:simpleType': {'xsd:restriction': ret}}

  if typ.name == 'dict':
    ret = dict()
    if typ.doc:
      ret['doc'] = typ.doc
    if typ.params and typ.params.value:
      for sub in typ.params.value:
        mergeNode(ret, _struct2schema(sub))
    return {'xsd:complexType': ret}

  if typ.name == Type.ONEOF:
    ret = dict()
    if typ.params and typ.params.value:
      for sub in typ.params.value:
        mergeNode(ret, _struct2schema(sub))
    ret = {'xsd:union': ret}
    if typ.doc:
      ret['doc'] = typ.doc
    return {'xsd:complexType': ret}

  if typ.name == 'list':
    # TODO: implement
    raise NotImplementedError('s2s for: %r' % (typ,))

  ret = dict(ref=_struct2ref(typ))
  if typ.doc:
    ret['doc'] = typ.doc
  return {'xsd:element': ret}

#------------------------------------------------------------------------------
def et2wadl(options, root):
  for ns, uri in wadl_xmlns.items():
    if ns == 'wadl':
      root.set('xmlns', uri)
    else:
      root.set('xmlns:' + ns, uri)
  root.set('xsi:schemaLocation', wadl_xmlns['wadl'] + ' wadl.xsd')
  rename = {
    'doc'               : 'doc:doc',
    'endpoint'          : 'resource',
    'return'            : 'representation',
    'raise'             : 'fault',
  }
  resources = ET.Element('resources')
  for elem in list(root):
    if elem.tag == 'endpoint':
      root.remove(elem)
      resources.append(elem)
  root.append(resources)
  appUrl = None
  for elem in root.iter():
    elem.tag = rename.get(elem.tag, elem.tag)
    if elem.tag == 'application' and 'url' in elem.attrib:
      appUrl = elem.attrib.pop('url')
    if elem.tag == 'resources' and appUrl:
      elem.set('base', appUrl)
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
  root.set('xmlns:app', appUrl or 'urn:application:' + str(uuid.uuid4()))
  return root

#------------------------------------------------------------------------------
# end of $Id$
# $ChangeLog$
#------------------------------------------------------------------------------
