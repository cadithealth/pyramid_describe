# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2014/05/07
# copy: (C) Copyright 2014-EOT Cadit Inc., All Rights Reserved.
#------------------------------------------------------------------------------

import re

from docutils import nodes
import asset

from ..typereg import Type, TypeRef

#------------------------------------------------------------------------------

docorator_cre   = re.compile(r'@([A-Z0-9_.-]+)(\([^)]*\))?', re.IGNORECASE)
notalphanum_cre = re.compile(r'[^A-Z0-9]+', re.IGNORECASE)

#------------------------------------------------------------------------------
def _extract(text):
  # todo: this will extract *all* the docorators in `text`,
  #       not just the ones at the beginning... fix!
  # TODO: the `docorator_cre` RE should *not* match 'foo@bar'...
  #       (but currently does)
  for match in docorator_cre.finditer(text):
    yield match.group(0)

#------------------------------------------------------------------------------
def _docorator2classes(label):
  label = label.lower()
  if '(' in label:
    cls = notalphanum_cre.sub('-', 'doc-' + label.split('(', 1)[0])
    if cls.endswith('-'):
      cls = cls[:-1]
    yield cls
  cls = notalphanum_cre.sub('-', 'doc-' + label)
  if cls.endswith('-'):
    cls = cls[:-1]
  yield cls

#------------------------------------------------------------------------------
def extract(text, raw=False):
  lbls = sorted(set(_extract(text)))
  clss = sorted(set([c for l in lbls for c in _docorator2classes(l)]))
  if raw:
    return (lbls, clss)
  return clss

#------------------------------------------------------------------------------
@asset.plugin('pyramid_describe.plugins.entry.parsers', 'docorator', after='numpydoc')
def entry_parser(entry, context):
  '''
  This pyramid-describe entry parser plugin extracts so-called
  "docorators" (documentation decorators, get it? ;-) from the
  documentation and adds them as classes to the decorated items. For
  example::

    @PUBLIC, @DEPRECATED(2.3)

    This is a public, but deprecated, method.

  will add the classes ``doc-public`` and ``doc-deprecated-2-3`` to
  the entry (if the docorators appear on the first line) or the
  current paragraph (if they appear within the non-first-paragraph
  documentation text).
  '''
  if not entry:
    return entry
  if entry.doc:
    entry.classes = ( entry.classes or [] ) \
      + extract(entry.doc.strip().split('\n\n')[0])
  return entry

#------------------------------------------------------------------------------
@asset.plugin('pyramid_describe.plugins.catalog.parsers', 'docorator', after='numpydoc')
def catalog_parser(catalog, context):
  for tname in catalog.typereg.typeNames():
    _docorateType(catalog.typereg, catalog.typereg.get(tname), force=True)
  for endpoint in catalog.endpoints:
    for method in endpoint.methods or []:
      _docorateEntry(catalog.typereg, method)
    _docorateEntry(catalog.typereg, endpoint)
  return catalog

#------------------------------------------------------------------------------
def _docorateEntry(typereg, entry):
  for attr in ('params', 'returns', 'raises'):
    _docorateType(typereg, getattr(entry, attr, None))
  entry.doc = _docorateText(entry.doc, skipfirst=True)

#------------------------------------------------------------------------------
def _docorateType(typereg, typ, force=False):
  if not typ:
    return
  if isinstance(typ, Type) and not force and typ is typereg.get(typ.name):
    return
  if isinstance(typ, TypeRef):
    _docorateType(typereg, typ.type)
  if typ.doc:
    docorators, classes = extract(typ.doc.strip().split('\n\n')[0], raw=True)
    if docorators:
      # todo: this may be problematic if the docorator has special chars...
      if isinstance(typ, TypeRef):
        # todo: *ideally*, these docorators would also be removed from
        #       the text if they are the only text in the first
        #       line...
        if not typ.params:
          typ.params = dict()
        for doco in docorators:
          typ.params[doco] = True
      # note: `Type`s don't have any params, so primary docorators are
      #       only promoted to `meta.classes`.
    if classes:
      if isinstance(typ, TypeRef):
        if not typ.params:
          typ.params = dict()
        typ.params['classes'] = sorted(set(typ.params.get('classes', []) + classes))
      else:
        typ.meta.classes = sorted(set((typ.meta.classes or []) + classes))
  typ.doc = _docorateText(typ.doc, skipfirst=True)
  for sub in typ.children:
    _docorateType(typereg, sub)
  if typ.params:
    classes = []
    for key, val in typ.params.items():
      if val is True and key.startswith('@'):
        classes += extract(key)
    if classes:
      typ.params['classes'] = sorted(set(typ.params.get('classes', []) + classes))

#------------------------------------------------------------------------------
def _docorateText(text, skipfirst=False):
  if not text:
    return text
  # todo: this is very primitive... *ideally* this would perform
  #       an rst-parse + rst-render roundtrip, *BUT*... there are
  #       significant issues with parsing an rst segment that may
  #       have internal links to other fragments not in `text`
  #       (because they are elsewhere in the documentation).
  # todo: also, it has the problem of not being idempotent, i.e.
  #       if called repeatedly on the same text, the text will
  #       have the classes added multiple times.
  # todo: what about indented sections?...
  while '\n\n\n' in text:
    text = text.replace('\n\n\n', '\n\n')
  parts = text.split('\n\n')
  ret   = []
  if skipfirst:
    ret.append(parts.pop(0))
  for part in parts:
    if part.startswith('@'):
      classes = extract(part)
      if classes:
        ret.append('.. class:: ' + ' '.join(classes))
    ret.append(part)
  return '\n\n'.join(ret)

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
