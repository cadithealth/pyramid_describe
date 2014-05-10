# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2014/05/07
# copy: (C) Copyright 2014-EOT Cadit Inc., All Rights Reserved.
#------------------------------------------------------------------------------

from __future__ import absolute_import

import re
from numpydoc.docscrape import NumpyDocString, Reader, dedent_lines

from ..util import adict
from ..describer import tag

#------------------------------------------------------------------------------

optional_cre = re.compile(r'(^|,)\s*optional\s*(?=,|$)', flags=re.IGNORECASE)
required_cre = re.compile(r'(^|,)\s*required\s*(?=,|$)', flags=re.IGNORECASE)
# todo: this does not allow a comma in the default... ugh.
default_cre  = re.compile(r'(?:^|,)\s*default:?\s+([^,]*)\s*(?=,|$)', flags=re.IGNORECASE)

#------------------------------------------------------------------------------
def consumeParams(ndoc, entry, options):
  nparams = ndoc['Parameters'] + ndoc['Other Parameters']
  if not nparams:
    return None
  params = []
  for nparam in nparams:
    param = adict(
      name     = nparam[0],
      type     = nparam[1],
      doc      = denumpify('\n'.join(nparam[2])),
      optional = False,
    )

    # *** HACK-ALERT *** HACK-ALERT *** HACK-ALERT *** HACK-ALERT ***
    # TODO: this is a total hack. the problem is that numpydoc assumes
    #       that, once a section is started, that everything until the
    #       next section is part of it... i.e. there is no 'stop!' tag...
    # TODO: one of the many problems with this particular solution is
    #       that the sections are then potentially rendered in the
    #       wrong order...
    if param.name.startswith(':doc.'):
      ndoc.hackalert = '\n\n' + param.name
      continue

    # parse out 'optional', 'required', and 'default'
    # => numpydoc should really have done this :(
    if optional_cre.search(param.type):
      param.optional = True
      param.type     = optional_cre.sub('', param.type)
    elif required_cre.search(param.type):
      param.optional = False
      param.type     = required_cre.sub('', param.type)
    if default_cre.search(param.type):
      param.optional = True
      param.default  = default_cre.search(param.type).group(1)
      param.type     = default_cre.sub('', param.type)
    # todo: shouldn't this have the method in the ID?... or is that
    #       already in `entry.path`?
    param.id = 'param-{}-{}'.format(tag(entry.path), tag(param.name))
    params.append(param)
  ndoc['Parameters'] = ndoc['Other Parameters'] = []
  return params

#------------------------------------------------------------------------------
def consumeReturns(ndoc, entry, options):
  if not ndoc['Returns']:
    return None
  ret = []
  for idx, nret in enumerate(ndoc['Returns']):
    node = adict(
      type = nret[1] or nret[0],
      doc  = denumpify('\n'.join(nret[2])),
    )
    # todo: shouldn't this have the method in the ID?... or is that
    #       already in `entry.path`?
    node.id = 'return-{}-{}-{}'.format(
      tag(entry.path),
      str(idx),
      tag(node.type))
    ret.append(node)
  ndoc['Returns'] = []
  return ret

#------------------------------------------------------------------------------
def consumeRaises(ndoc, entry, options):
  if not ndoc['Raises']:
    return None
  ret = []
  for idx, nrz in enumerate(ndoc['Raises']):
    node = adict(
      type  = nrz[1] or nrz[0],
      doc   = denumpify('\n'.join(nrz[2])),
    )
    # todo: shouldn't this have the method in the ID?... or is that
    #       already in `entry.path`?
    node.id = 'raise-{}-{}-{}'.format(
      tag(entry.path),
      str(idx),
      tag(node.type))
    ret.append(node)
  ndoc['Raises'] = []
  return ret

#------------------------------------------------------------------------------
SECTIONCHARS = '''=-`:'"~^_*+#<>'''
def sectionTitle(title, level=None, char=None, top=None):
  if level is None and char is None:
    level = 0
  if char is None:
    char = SECTIONCHARS[level % len(SECTIONCHARS)]
  if top is None and level is not None:
    top = level < len(SECTIONCHARS)
  if len(title) > 0 and title == title[0] * len(title) and re.match('[^a-zA-Z0-9]', title[0]):
    title = re.sub('([^a-zA-Z0-9])', '\\\\\\1', title)
  # note setting minimum of 6 under/over chars since ":::" (e.g. when
  # title is "PUT") seems to have problems...
  ret = char * max(6, len(title))
  if top:
    ret = [ret, title, ret]
  else:
    ret = [title, ret]
  return '\n'.join(ret)

#------------------------------------------------------------------------------
def denumpify(text, level=0):
  # TODO: this is a very brittle implementation... ideally, the
  #       docutils rst parser would be extended to support the
  #       numpy-style attribute definitions... not likely though.
  rdr = Reader(text.strip())
  ret = ''
  while not rdr.eof():
    line = rdr.read()
    if not line.strip():
      if not ret or line != '' or not ret.endswith('\n\n'):
        ret += line + '\n'
      continue
    if ' : ' not in line:
      line = [line]
      if rdr.peek():
        line.extend(rdr.read_to_next_empty_line())
      ret += '\n'.join(line) + '\n'
      continue
    if ret and not ret.endswith('\n\n'):
      ret += '\n'
    attr_name, attr_spec = line.split(' : ', 1)
    attr_name = sectionTitle(attr_name, level=level)
    desc = '\n'.join(dedent_lines(rdr.read_to_next_unindented_line())).strip()
    ret += '\n\n'.join([
      '.. class:: attr',
      attr_name,
      '.. class:: spec',
      attr_spec,
      '', # force terminal '\n\n'
    ])
    if desc:
      ret += denumpify(desc, level=level + 1).strip() + '\n'
  return ret

#------------------------------------------------------------------------------
def parser(entry, options):

  if not entry or not entry.doc:
    return entry

  ndoc = NumpyDocString(entry.doc)
  entry.params  = consumeParams(ndoc, entry, options)   or entry.params
  entry.returns = consumeReturns(ndoc, entry, options)  or entry.returns
  entry.raises  = consumeRaises(ndoc, entry, options)   or entry.raises
  # todo: anything to do with 'Warns', 'Attributes', 'Methods' ?...

  # this re-assembles everything that was not consumed and removes
  # the index if empty.
  entry.doc = str(ndoc).strip()
  # todo: is there no way to disable the index generation?...
  if entry.doc.endswith('.. index::'):
    entry.doc = entry.doc[: - len('.. index::')].strip()

  # TODO: this is the continuation of the HACK-ALERT in `consume*()`...
  if getattr(ndoc, 'hackalert', False):
    entry.doc += ndoc.hackalert

  return entry

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
