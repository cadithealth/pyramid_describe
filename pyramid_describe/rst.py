# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2013/09/17
# copy: (C) Copyright 2013 Cadit Health Inc., All Rights Reserved.
#------------------------------------------------------------------------------

import sys, re
from pyramid.settings import aslist
from pyramid.path import AssetResolver, DottedNameResolver
from docutils import nodes, core, io
from docutils.parsers.rst import Directive, directives
from docutils.transforms import misc
from six.moves import urllib

from .util import resolve, runFilters

#------------------------------------------------------------------------------
# TODO: don't do this. instead, open a feature-request...
from docutils.writers.html4css1 import HTMLTranslator
def better_stylesheet_call(self, path):
  # check for whether or not the css path starts with
  # 'data:text/css' in which case it is treated as an inlined
  # stylesheet instead of a filename.
  upath = urllib.parse.unquote(path or '')
  if not upath or not upath.startswith('data:text/css'):
    return self._real_stylesheet_call(path)
  content = upath.split(',', 1)[1]
  return self.embedded_stylesheet % (content,)
def better_starttag(self, node, tagname, *args, **kw):
  # removes redundant 'classes' from nodes
  if hasattr(node, 'attributes'):
    node['classes'] = sorted(set(node.get('classes', [])))
    if kw.get('CLASS') in node['classes']:
      kw.pop('CLASS', None)
    if kw.get('class') in node['classes']:
      kw.pop('class', None)
  return self._real_starttag(node, tagname, *args, **kw)
def better_visit_list_item(self, node):
  # removes redundant 'first' class, if present
  self._real_visit_list_item(node)
  if len(node):
    node[0]['classes'] = list(set(node[0]['classes']))
if not hasattr(HTMLTranslator, '_real_stylesheet_call'):
  HTMLTranslator._real_stylesheet_call = HTMLTranslator.stylesheet_call
  HTMLTranslator.stylesheet_call = better_stylesheet_call
if not hasattr(HTMLTranslator, '_real_starttag'):
  HTMLTranslator._real_starttag = HTMLTranslator.starttag
  HTMLTranslator.starttag = better_starttag
if not hasattr(HTMLTranslator, '_real_visit_list_item'):
  HTMLTranslator._real_visit_list_item = HTMLTranslator.visit_list_item
  HTMLTranslator.visit_list_item = better_visit_list_item
# /TODO
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
# TODO: this is a total hack. instead, there should be a
#       publish_parts_from_doctree(), and that should be filterable...
# TODO: is there perhaps a better, more "docutils-ish", way to do this?...
class AsIs(nodes.raw):
  def __init__(self, content, *children, **attributes):
    nodes.FixedTextElement.__init__(
      self, content, content, *children, **attributes)
def html_visit_AsIs(self, node):
  self.body.append(node.astext())
  raise nodes.SkipChildren()
def html_depart_AsIs(self, node):
  pass
if not hasattr(HTMLTranslator, 'visit_AsIs'):
  HTMLTranslator.visit_AsIs = html_visit_AsIs
if not hasattr(HTMLTranslator, 'depart_AsIs'):
  HTMLTranslator.depart_AsIs = html_depart_AsIs
# /TODO
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
def resolvecss(data, spec):
  if ':' in spec:
    pkg, name = spec.split(':', 1)
    return AssetResolver(pkg).resolve(name).stream().read()
  return resolve(spec)(data)

#------------------------------------------------------------------------------
class HtmlDoctreeFixer():
  def __init__(self, document):
    self.document = document
  def dispatch_visit(self, node):
    if not hasattr(node, 'attributes'):
      return
    if isinstance(node, nodes.title) \
        and isinstance(node.parent, nodes.section) \
        and 'section-title' not in node['classes']:
      node['classes'].append('section-title')
    ids = node.get('ids', [])
    if len(ids) > 1:
      node['ids'] = node['ids'][1:]

#------------------------------------------------------------------------------
def rst2html(data, text):

  css = [
    urllib.parse.quote('data:text/css;charset=UTF-8,' + resolvecss(data, e))
    for e in aslist(data.options.cssPath or '')]
  # todo: add the docutils default css as well...

  settings = dict(
    # input_encoding     = 'UTF-8',
    output_encoding      = data.options.encoding,
    embed_stylesheet     = data.options.cssEmbed,
    stylesheet_path      = css,
    doctitle_xform       = False,
    sectsubtitle_xform   = False,
    )

  pub = core.Publisher(None, None, None,
                       source_class=io.StringInput,
                       destination_class=io.NullOutput)
  pub.set_components('standalone', 'restructuredtext', 'html')
  pub.process_programmatic_settings(None, settings, None)
  pub.set_source(text, None)
  pub.set_destination(None, None)
  pub.publish(enable_exit_status=False)

  doc = pub.document
  doc.walk(HtmlDoctreeFixer(doc))
  doc = runFilters(data.options.filters, doc, data)

  html = core.publish_from_doctree(
    pub.document, writer_name='html', settings_overrides=settings)

  return html

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
