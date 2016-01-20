# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2016/01/05
# copy: (C) Copyright 2016-EOT Cadit Inc., All Rights Reserved.
#------------------------------------------------------------------------------

'''
This module provides an enhanced NumpyDocString that fixes certain
issues with the current implementation wrt pyramid_describe's
documentation extraction requirements.
'''

from numpydoc.docscrape import NumpyDocString, Reader

#------------------------------------------------------------------------------
class FixedReader(Reader):
  # TODO: see `FixedNumpyDocString`
  def read_to_next_empty_line(self):
    return super(FixedReader, self).read_to_next_empty_line() + ['']

#------------------------------------------------------------------------------
class FixedNumpyDocString(NumpyDocString):
  #----------------------------------------------------------------------------
  # TODO: patch numpydoc with these two changes...
  #       1) adds awareness to stringify that a parameter's description
  #          is optional, and only one of its name or value is required
  #       2) does not output an empty index during stringify
  #       3) preserve empty lines (for rST paragraph detection) by using
  #          FixedReader
  #       4) strip trailing whitespace
  #       5) collapse multiple empty lines into one
  #----------------------------------------------------------------------------
  # TODO: more possible ways to improve NumpyDocString:
  #       1) allow attr declaration to be whitespace separated, not just
  #          space separated. e.g. these should be handled identically:
  #          * ``key : value``
  #          * ``key\t:\tvalue``
  #----------------------------------------------------------------------------
  def __init__(self, docstring, *args, **kw):
    from numpydoc.docscrape import textwrap
    super(FixedNumpyDocString, self).__init__('', *args, **kw)
    docstring = textwrap.dedent(docstring).split('\n')
    self._doc = FixedReader(docstring)
    self._parse()
  def _str_param_list(self, name):
    out = []
    if self[name]:
      out += self._str_header(name)
      # todo: this feels so much "cleaner"...
      # out += ['']
      for param, param_type, desc in self[name]:
        out += [' : '.join(filter(None, [param, param_type]))]
        if desc != ['']:
          out += self._str_indent(desc)
      out += ['']
    return out
  def _str_index(self):
    ret = super(FixedNumpyDocString, self)._str_index()
    if ret == ['.. index:: ']:
      return []
    return ret
  def __str__(self, *args, **kw):
    ret = super(FixedNumpyDocString, self).__str__(*args, **kw)
    ret = '\n'.join(line.rstrip() for line in ( ret or '' ).split('\n'))
    while '\n\n\n' in ret:
      ret = ret.replace('\n\n\n', '\n\n')
    return ret.strip()

#------------------------------------------------------------------------------
def _text2numpylines(text):
  # todo: this is a *ridiculous* way of doing this...
  ndoc = FixedNumpyDocString('Returns\n-------\n\n' + text)
  # todo: if more than one section is extracted, coallesce them...
  #       but how to determine order???
  # todo: this is definitely violating the numpydoc API barrier...
  sections = [key for key in ndoc.__dict__['_parsed_data'].keys()
              if ndoc[key] and ndoc[key] != [''] and key != 'Returns']
  if sections:
    raise ValueError('unexpected/invalid nested section(s): %s'
                     % (', '.join(repr(s) for s in sections),))
  return list(ndoc['Returns'])

#------------------------------------------------------------------------------
def _numpylines2text(nlines):
  # todo: this is a *ridiculous* way of doing this...
  ndoc = FixedNumpyDocString('')
  ndoc['Returns'] = nlines
  ret = str(ndoc).strip()
  if not ret:
    return ret
  marker = 'Returns\n-------\n'
  if not ret.startswith(marker):
    raise ValueError(
      'unexpected "Returns" beginning marker missing: %r' % (ret,))
  ret = ret[len(marker):].strip()
  return ret

#------------------------------------------------------------------------------
def decomment(text, commentToken):
  '''
  **Try not to use this**.

  Why? Well, this really should be done "inline" so that
  context-sensitivity can be implemented. for example, the following
  numpydoc would not be parsed as expected::

    Returns:
    --------
    value : ( number | "some ## weird ## string" )
  '''
  return '\n'.join(
    line.split(commentToken)[0].rstrip()
    for line in text.split('\n'))

#------------------------------------------------------------------------------
# end of $Id$
# $ChangeLog$
#------------------------------------------------------------------------------
