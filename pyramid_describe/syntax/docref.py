# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2014/05/06
# copy: (C) Copyright 2014-EOT Cadit Inc., All Rights Reserved.
#------------------------------------------------------------------------------

import six
import os.path
import docutils
from docutils import nodes
from docutils.parsers.rst import roles
from docutils.writers.html4css1 import HTMLTranslator
import re
import pkg_resources

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
def parser(entry, options):
  if not entry:
    return entry
  entry.doc = resolveImports(entry.doc, entry, options)
  return entry

#------------------------------------------------------------------------------
docimport_cre = re.compile(':doc\.import:`([^`]+)`')
def resolveImports(text, entry, options):
  # note: not using rST to parse the text because it may not be "rST"
  #       compliant yet... (docref.parser is called first in the
  #       chain).
  if not text:
    return text
  if ':doc.import:' not in text:
    return text
  def _resolve(match):
    return resolveImport(match.group(1), entry, options)
  return docimport_cre.sub(_resolve, text)

#------------------------------------------------------------------------------
def resolveImport(spec, entry, options):
  try:
    try:
      return resolveImportAsset(spec, entry, options)
    except:
      return resolveImportSymbol(spec, entry, options)
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
def resolveImportAsset(spec, entry, options):
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
def resolveImportSymbol(spec, entry, options):
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
# doc.link
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
class pyrdesc_doc_link(nodes.reference): pass
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
  def _escapeTextRoleArg(self, text):
    # todo: anything else need escaping?...
    return '`' + text.replace('\\', '\\\\').replace('`', '\\`') + '`'
  @property
  def args(self):
    args = [self.dpath]
    if self.method:
      args.insert(0, self.method)
    return args
  def __str__(self):
    return ':' + self._name + ':' + self._escapeTextRoleArg(':'.join(self.args))
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
# doc.copy
#------------------------------------------------------------------------------

# todo: support something like
#         :doc.copy:`METHOD:PATH:Parameters` -- copies title & all params
#         :doc.copy:`METHOD:PATH:Parameters[.*]` -- copies all params only
#         :doc.copy:`METHOD:PATH:Parameters[(foo|bar)]` -- copies 'foo' & 'bar' params only

# TODO: doc.copy's are currently child nodes of nodes.paragraph... which it
#       really shouldn't be. instead, it should be a nodes.container (or
#       something similar. one of the problems this causes is that the HTML
#       output wraps the imported nodes with a redundant <p>...</p>. ugh.
#       ==> perhaps doc.copy should be a "directive" (instead of a "role")?

#------------------------------------------------------------------------------
class pyrdesc_doc_copy(nodes.reference): pass
roles.register_generic_role('doc.copy', pyrdesc_doc_copy)

#------------------------------------------------------------------------------
class DocCopy(DocLink):
  _name = 'doc.copy'
  def __init__(self, spec, node):
    '''
    Valid `spec` format EBNF := [ METHOD ':' ] PATH [ ':' SECTION ]
    '''
    if not spec or not isinstance(spec, six.string_types):
      raise ValueError(
        'Invalid pyramid-describe "%s" target: %r' % (self._name, spec))
    specv = spec.split(':')
    if len(specv) > 3:
      raise ValueError(
        'Invalid pyramid-describe "%s" target: %r' % (self._name, spec))
    self.sections = specv.pop().split(',') if len(specv) > 2 else None
    super(DocCopy, self).__init__(':'.join(specv), node)
    self.spec = spec
  @property
  def args(self):
    args = [self.dpath]
    if self.method or self.sections:
      args.insert(0, self.method or '')
    if self.sections:
      args.append(','.join(self.sections))
    return args
def pyrdesc_doc_copy_rst_visit(self, node):
  self._pushOutput()
def pyrdesc_doc_copy_rst_depart(self, node):
  copy = DocCopy(self._popOutput().data(), node)
  self.output.separator()
  self.output.append(str(copy))
  self.output.separator()
RstTranslator.visit_pyrdesc_doc_copy = pyrdesc_doc_copy_rst_visit
RstTranslator.depart_pyrdesc_doc_copy = pyrdesc_doc_copy_rst_depart

#------------------------------------------------------------------------------
def findPath(node, path, up=True):
  # TODO: doc.copy's should probably be de-referenced on the parse-side instead
  #       of the render-side, since that would centralize where that kind of
  #       processing needs to occur... *AND* it would remove the need for this
  #       function, which is a *very* odd one...
  #       ==> note that this would have to be a two-phase thing if done parse-
  #           side, since a doc.copy may reference a URL that has not been
  #           loaded yet.
  if not node:
    return None
  if up:
    path = 'endpoint-' + tag(path)
    while node.parent:
      node = node.parent
    return findPath(node, path, False)
  for sub in walk(node):
    if isinstance(sub, nodes.section) \
        and 'endpoint' in getattr(sub, 'attributes', {}).get('classes', []) \
        and path in sub.attributes.get('ids', []):
      return sub
  return None

#------------------------------------------------------------------------------
def findMethod(node, path, method):
  if not node:
    return None
  if not method:
    # TODO: fallback to 'GET'?
    return node
  nid = 'method-' + tag(path) + '-' + tag(method)
  for sub in walk(node):
    # todo: the `method.lower()` feels a bit weird to me... it's a bit of
    #       an abstraction barrier violation. i should
    if isinstance(sub, nodes.section) \
        and 'method' in getattr(sub, 'attributes', {}).get('classes', []) \
        and nid in sub.attributes.get('ids', []):
      return sub
  return None

#------------------------------------------------------------------------------
def findSection(node, path, method, section):
  if not node:
    return None
  klass = section.lower()
  if klass == 'parameters':
    klass = 'params'
  nid = klass + '-method-' + tag(path) + '-' + tag(method)
  for sub in walk(node):
    if isinstance(sub, nodes.section) \
        and klass in getattr(sub, 'attributes', {}).get('classes', []) \
        and nid in sub.attributes.get('ids', []):
      return sub
  return None

#------------------------------------------------------------------------------
def pyrdesc_doc_copy_html_visit(self, node):
  text  = node.astext()
  copy  = DocCopy(text, node)
  cnode = findPath(node, copy.path)
  if not cnode:
    raise ValueError(
      'Could not find "doc.copy" path target for "%s"' % (text,))
  cnode = findMethod(cnode, copy.path, copy.method)
  if not cnode:
    raise ValueError(
      'Could not find "doc.copy" method target for "%s"' % (text,))
  if not copy.sections or '*' in copy.sections:
    wild = copy.sections and '*' in copy.sections
    # TODO: should this just be ``for idx, child in enumerate(cnode):`` ?
    for idx, child in enumerate(cnode.children):
      # todo: why is this check for 'html.MetaBody.meta' necessary???
      #       i.e. how is it being excluded during the normal walk of
      #       the remote node but not here?...
      from docutils.parsers.rst.directives import html
      if ( idx == 0 and isinstance(child, nodes.title) ) \
          or isinstance(child, html.MetaBody.meta):
        continue
      if wild:
        if 'section' not in child.attributes['classes']:
          continue
      child.walkabout(self)
    raise nodes.SkipNode
  # todo: here, the :doc.copy: is controlling order, but that probably
  #       shouldn't be the case, since order of sections is not
  #       preserved by the numpydoc parsing.
  for section in copy.sections:
    snode = findSection(cnode, copy.path, copy.method, section)
    if not snode:
      raise ValueError(
        'Could not find "doc.copy" section target "%s" for "%s"'
        % (section, text,))
    snode.walkabout(self)
  raise nodes.SkipNode
def pyrdesc_doc_copy_html_depart(self, node):
  pass
HTMLTranslator.visit_pyrdesc_doc_copy = pyrdesc_doc_copy_html_visit
HTMLTranslator.depart_pyrdesc_doc_copy = pyrdesc_doc_copy_html_depart

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
