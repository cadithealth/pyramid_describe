# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2014/05/06
# copy: (C) Copyright 2014-EOT Cadit Inc., All Rights Reserved.
#------------------------------------------------------------------------------

import os.path
import re

import six
import docutils
from docutils import nodes
from docutils.parsers.rst import roles
from docutils.writers.html4css1 import HTMLTranslator
import pkg_resources
import asset

from ..writers.rst import RstTranslator
from ..describer import tag
from ..resolve import resolve
from ..doctree import walk

#------------------------------------------------------------------------------

# TODO: remove the global-level polution of the `roles` registrations
#       (of **all** roles)

# TODO: there currently is no detection of doc.link references to
#       endpoints/methods that don't exist

#------------------------------------------------------------------------------
@asset.plugin('pyramid_describe.plugins.entry.parsers', 'docref')
def parser(entry, context):
  if not entry:
    return entry
  entry.doc = resolveImports(entry.doc, entry, context)
  return entry

#------------------------------------------------------------------------------
docimport_cre = re.compile(':doc\.import:`([^`]+)`')
def resolveImports(text, entry, context):
  # note: not using rST to parse the text because it may not be "rST"
  #       compliant yet... (docref.parser is called first in the
  #       chain).
  if not text:
    return text
  if ':doc.import:' not in text:
    return text
  def _resolve(match):
    return resolveImport(match.group(1), entry, context)
  return docimport_cre.sub(_resolve, text)

#------------------------------------------------------------------------------
def resolveImport(spec, entry, context):
  try:
    try:
      return resolveImportAsset(spec, entry, context)
    except:
      return resolveImportSymbol(spec, entry, context)
  except:
    raise ValueError(
      'Invalid pyramid-describe "doc.import" target from %r: %r'
      % (entry.dpath, spec,))

#------------------------------------------------------------------------------
def getModuleParent(modname):
  mod = resolve(modname)
  if not mod.__file__ or '/__init__.' in mod.__file__:
    return modname
  return '.'.join(modname.split('.')[:-1])

#------------------------------------------------------------------------------
pkg_cre = re.compile('^([a-z0-9._]+):', re.IGNORECASE)
def resolveImportAsset(spec, entry, context):
  pkg = pkg_cre.match(spec)
  if not pkg:
    pkg  = getModuleParent(entry.view.__module__)
    path = ''
    if '.' in pkg:
      pkg, path = pkg.split('.', 1)
    path = os.path.normpath(os.path.join(path.replace('.', '/'), spec))
  else:
    pkg  = pkg.group(1)
    path = spec.split(':', 1)[1]
  return pkg_resources.resource_string(pkg, path)

#------------------------------------------------------------------------------
def resolveImportSymbol(spec, entry, context):
  # todo: ugh. this is yucky... there must be a better way of
  #       resolving relative module names...
  count = 0
  while spec.startswith('.'):
    spec  = spec[1:]
    count += 1
  if count > 0:
    parent = getModuleParent(entry.view.__module__)
    if count > 1:
      parent = '.'.join(parent.split('.')[:1 - count])
    if parent:
      parent += '.'
    spec = parent + spec
  symbol = resolve(spec)
  return symbol() if callable(symbol) else str(symbol)

#------------------------------------------------------------------------------
# TODO: provide a better implementation here...
# todo: or move to using inline-style declaration? (that way it does not
#       polute *everything* in the application):
#         .. role:: class(literal)
#         .. role:: meth(literal)
#         .. role:: func(literal)
roles.register_generic_role('class', nodes.literal)
roles.register_generic_role('meth', nodes.literal)
roles.register_generic_role('func', nodes.literal)
# /TODO
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
def undecorate(path):
  # this is very dim-witted implementation, but it works...
  # todo: is there a way to get rid of the need for this?...
  #       perhaps by using entry.path instead of entry.dpath...
  for char in '{}<>':
    path = path.replace(char, '')
  return path

#------------------------------------------------------------------------------
def resolvePath(path, node):
  if path.startswith('/'):
    return os.path.normpath(path)
  curpath = None
  while node.parent:
    node = node.parent
    if not isinstance(node, nodes.section) or not hasattr(node, 'attributes'):
      continue
    curpath = node.attributes.get('dpath', '') \
      or node.attributes.get('path', '') \
      or curpath
    if curpath:
      break
    if 'endpoint' in node.attributes.get('classes', ''):
      for nid in node.attributes['ids']:
        if nid.startswith('endpoint-'):
          curpath = nid.split('-')[1].decode('hex')
          break
      break
  if not curpath:
    raise ValueError(
      'Could not find current location for relative path "%s"' % (path,))
  return os.path.normpath(os.path.join(curpath, path))

#------------------------------------------------------------------------------
def toTextRoleArg(text):
  # todo: anything else need escaping?...
  return '`' + text.replace('\\', '\\\\').replace('`', '\\`') + '`'

#------------------------------------------------------------------------------
# doc.link
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
class pyrdesc_doc_link(nodes.reference): pass
textrole_doc_link = pyrdesc_doc_link
roles.register_generic_role('doc.link', pyrdesc_doc_link)

#------------------------------------------------------------------------------
class DocLink(object):
  _name = 'doc.link'
  def __init__(self, spec, node):
    '''
    Valid `spec` format EBNF := [ METHOD ':' ] PATH
    '''
    self.spec = spec
    if not spec or not isinstance(spec, six.string_types):
      raise ValueError(
        'Invalid pyramid-describe "%s" target: %r' % (self._name, spec))
    specv = spec.split(':')
    if len(specv) > 2:
      raise ValueError(
        'Invalid pyramid-describe "%s" target: %r' % (self._name, spec))
    self.dpath  = resolvePath(specv.pop(), node)
    self.path   = undecorate(self.dpath)
    self.method = specv.pop() if specv else None
  @property
  def args(self):
    args = [self.dpath]
    if self.method:
      args.insert(0, self.method)
    return args
  def __str__(self):
    return ':' + self._name + ':' + toTextRoleArg(':'.join(self.args))
def pyrdesc_doc_link_rst_visit(self, node):
  self._pushOutput()
def pyrdesc_doc_link_rst_depart(self, node):
  link = DocLink(self._popOutput().data(), node)
  self.output.separator()
  self.output.append(str(link))
  self.output.separator()
RstTranslator.visit_pyrdesc_doc_link = pyrdesc_doc_link_rst_visit
RstTranslator.depart_pyrdesc_doc_link = pyrdesc_doc_link_rst_depart

#------------------------------------------------------------------------------
def pyrdesc_doc_link_html_visit(self, node):
  # todo: make this 'doc-' prefix configurable...
  atts = {'class': 'doc-link'}
  link = DocLink(node.astext(), node)
  if not link.method:
    atts['href']  = '#endpoint-' + tag(link.path)
    atts['class'] += ' endpoint'
  else:
    atts['href'] = '#method-' + tag(link.path) + '-' + tag(link.method)
    atts['class'] += ' method'
  self.body.append(self.starttag(node, 'a', '', **atts))
def pyrdesc_doc_link_html_depart(self, node):
  self.body.append('</a>')
  if not isinstance(node.parent, nodes.TextElement):
    self.body.append('\n')
HTMLTranslator.visit_pyrdesc_doc_link = pyrdesc_doc_link_html_visit
HTMLTranslator.depart_pyrdesc_doc_link = pyrdesc_doc_link_html_depart

#------------------------------------------------------------------------------
# doc.type
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
class pyrdesc_doc_type(nodes.reference): pass
textrole_doc_type = pyrdesc_doc_type
roles.register_generic_role('doc.type', pyrdesc_doc_type)

#------------------------------------------------------------------------------
class DocType(object):
  _name = 'doc.type'
  def __init__(self, target, node):
    self.target = target
    if not target or not isinstance(target, six.string_types):
      raise ValueError(
        'Invalid pyramid-describe "%s" target: %r' % (self._name, target))
  def __str__(self):
    return ':' + self._name + ':' + toTextRoleArg(self.target)
def pyrdesc_doc_type_rst_visit(self, node):
  self._pushOutput()
def pyrdesc_doc_type_rst_depart(self, node):
  type = DocType(self._popOutput().data(), node)
  self.output.separator()
  self.output.append(str(type))
  self.output.separator()
RstTranslator.visit_pyrdesc_doc_type = pyrdesc_doc_type_rst_visit
RstTranslator.depart_pyrdesc_doc_type = pyrdesc_doc_type_rst_depart

#------------------------------------------------------------------------------
def pyrdesc_doc_type_html_visit(self, node):
  # todo: make this 'doc-' prefix configurable...
  type = DocType(node.astext(), node)
  atts = {
    'class' : 'doc-typeref',
    'href'  : '#typereg-type-' + tag(type.target),
  }
  self.body.append(self.starttag(node, 'a', '', **atts))
def pyrdesc_doc_type_html_depart(self, node):
  self.body.append('</a>')
  if not isinstance(node.parent, nodes.TextElement):
    self.body.append('\n')
HTMLTranslator.visit_pyrdesc_doc_type = pyrdesc_doc_type_html_visit
HTMLTranslator.depart_pyrdesc_doc_type = pyrdesc_doc_type_html_depart

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
