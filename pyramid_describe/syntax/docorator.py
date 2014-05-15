# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2014/05/07
# copy: (C) Copyright 2014-EOT Cadit Inc., All Rights Reserved.
#------------------------------------------------------------------------------

import re
from docutils import nodes

#------------------------------------------------------------------------------

docorator_cre   = re.compile(r'@([A-Z0-9_.-]+)(\([^)]*\))?', re.IGNORECASE)
notalphanum_cre = re.compile(r'[^A-Z0-9]+', re.IGNORECASE)

#------------------------------------------------------------------------------
def extract(text):
  for match in docorator_cre.finditer(text):
    # todo: make this 'doc-' prefix configurable...
    cls = notalphanum_cre.sub('-', 'doc-' + match.group(1).lower())
    if cls.endswith('-'):
      cls = cls[:-1]
    yield cls
    if not match.group(2):
      continue
    cls = notalphanum_cre.sub('-', 'doc-' + match.group(0)[1:].lower())
    if cls.endswith('-'):
      cls = cls[:-1]
    yield cls

#------------------------------------------------------------------------------
def parser(entry, options):
  if not entry:
    return entry
  if entry.doc:
    entry.classes = ( entry.classes or [] ) \
      + list(set(extract(entry.doc.strip().split('\n\n')[0])))
  for attr in 'params', 'returns', 'raises':
    for item in ( getattr(entry, attr, []) or [] ):
      clist = list(set(extract(item.type or '')))
      if clist:
        item.classes = ( item.classes or [] ) + clist
  return entry


#------------------------------------------------------------------------------
# <HACK-ALERT>
# TODO: remove this hack; basically, the docorator parsing is being
#       done here *again* in order to avoid needing to parse (and thus
#       render) the rST during `entries.parsers` handling... ugh. some
#       possible solutions:
#         * use doctree as the native format for the describer (ugh)
#         * do a rstParse-analyze-rstRender roundtrip on the docs (ugh)
#         * make the entry.doc be a doctree object, changing the API (ugh)
#       the last is probably the best, but yuck. maybe it can be an
#       encapsulated object that auto-renders itself if accessed as a
#       string (and invalidates the doctree if set to a string). but
#       that increases the roundtrips for all unaware callables. (ugh)
#
#       ===> NOTE: numpydoc's parser() is already parsing the
#       document...  is there perhaps a way to share that here?...
#
# </HACK-ALERT>
def postParser(doc):
  walktree(doc)
  return doc
def walktree(node):
  if not node or not isinstance(node, nodes.Node):
    return
  decorate(node)
  for snode in node:
    walktree(snode)
def decorate(node):
  if not isinstance(node, nodes.paragraph) \
      or not node.astext().startswith('@'):
    return
  if node.parent and isinstance(node.parent, nodes.section):
    children = node.parent.children
    if ( len(children) > 0 and node is children[0] ) \
        or ( len(children) > 1 and node is children[1]
             and isinstance(children[0], nodes.title) ):
      return
  # todo: this will extract *all* the docorators in the paragraph,
  #       not just the ones at the beginning... fix!
  clist = list(set(extract(node.astext())))
  if clist:
    if 'classes' not in node.attributes:
      node.attributes['classes'] = []
    node.attributes['classes'].extend(clist)

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
