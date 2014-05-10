# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2014/05/07
# copy: (C) Copyright 2014-EOT Cadit Inc., All Rights Reserved.
#------------------------------------------------------------------------------

from __future__ import absolute_import

from numpydoc.docscrape import NumpyDocString

#------------------------------------------------------------------------------
_sectnames = None
def getNames():
  # for reference: at the time of this writing, the list of names was:
  #   Methods, Parameters, Warnings, Warns, Other Parameters, Summary,
  #   Returns, References, Examples, Signature, Raises, Attributes,
  #   See Also, Notes, Extended Summary
  global _sectnames
  if _sectnames is None:
    _sectnames = set(NumpyDocString('')._parsed_data.keys())
    _sectnames -= set(['index'])
    _sectnames |= set(['Parameters', 'Returns', 'Raises'])
  return _sectnames

#------------------------------------------------------------------------------
def normLines(text):
  if not text:
    return text
  return str(text).replace('\r\n', '\n').replace('\r', '\n')

#------------------------------------------------------------------------------
def parser(entry, options):
  if not entry or not entry.doc:
    return entry
  doc = normLines(entry.doc).strip()
  for name in getNames():
    lbl  = ':' + name + ':'
    line = '-' * max(6, len(name))
    doc  = doc.replace('\n\n' + lbl + '\n\n',
                       '\n\n' + name + '\n' + line + '\n\n')
    if doc.startswith(lbl + '\n\n'):
      doc = name + '\n' + line + doc[len(lbl):]
    if doc.endswith('\n\n' + lbl):
      doc = doc[: - len(lbl)] + name + '\n' + line
  entry.doc = doc
  return entry

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
