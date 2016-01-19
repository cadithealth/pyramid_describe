# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2015/12/28
# copy: (C) Copyright 2015-EOT Cadit Inc., All Rights Reserved.
#------------------------------------------------------------------------------

import logging
import json
import textwrap

from ...typereg import TypeRegistry, Type, TypeRef
from ...params import parse as parseParams
from .extractor import _numpylines2text as numpylines2text
from .extractor import _text2numpylines as text2numpylines
from .extractor import decomment

#------------------------------------------------------------------------------

log = logging.getLogger(__name__)

DEFAULT_COMMENT_TOKEN = TypeRegistry.DEFAULT_OPTIONS['commentToken']

# TODO: get rid of this!
_typereg = TypeRegistry()

#------------------------------------------------------------------------------
def parseSpec(context, spec):
  '''
  DEPRECATED. this should be replaced by a "native" `Parser.parseSpec`...
  '''
  # TODO: move typespec parsing from typereg to here...
  typ, par = context.options.typereg.parseType(spec, complete=False)
  if par:
    par = par.strip()
    if not par.startswith(','):
      raise ValueError('invalid type specification: %r' % (spec,))
    par = parseParams(par[1:])
  return (typ, par or None)

#------------------------------------------------------------------------------
def _could_be_a_type(value):
  # todo: currently it only supports something like:
  #         Person
  #       it would be nice to support something like this too:
  #         list(ref(Thing))
  #       ==> use the TypeRegistry to parse it and see if it resolves???
  #       ==> or, at the very minimum, parse the first token and see if
  #           it is in the TypeManager's scalars, aliases, or declared
  #           types...
  #       ==> this should really not need to depend on the TypeRegistry...
  return bool(_typereg.isType(value))

#------------------------------------------------------------------------------
def parseNumpyMulti(nlines):
  return Parser().parseNumpyMulti(nlines)

#------------------------------------------------------------------------------
def parseNumpy(nlines):
  return Parser().parseNumpy(nlines)

#------------------------------------------------------------------------------
def parseMulti(text):
  return Parser().parseMulti(text)

#------------------------------------------------------------------------------
def parse(text):
  return Parser().parse(text)

#------------------------------------------------------------------------------
class Parser(object):

  #----------------------------------------------------------------------------
  def __init__(self, comment=DEFAULT_COMMENT_TOKEN, *args, **kw):
    super(Parser, self).__init__(*args, **kw)
    self.comment = comment

  #----------------------------------------------------------------------------
  def parse(self, text, eager=False):
    res = list(self.parseMulti(text, eager=eager))
    if not res:
      return res
    if len(res) > 1:
      for item in res:
        if not isinstance(item[1], TypeRef):
          raise ValueError(
            'context does not support multi-types: %r' % (text,))
    doc = None
    typ = None
    for idx, item in enumerate(res):
      if idx == 0:
        doc = item[0]
        typ = item[1]
        if isinstance(typ, TypeRef):
          typ = Type(base=Type.COMPOUND, name=Type.DICT, value=[typ])
      else:
        if item[0]:
          raise ValueError(
            'context does not support interleaved text: %r' % (item[0],))
        typ.value.append(item[1])
    return doc or None, typ
  #----------------------------------------------------------------------------
  def parseMulti(self, text, eager=False):
    # todo: this really shouldn't be done "globally" like this... i.e.
    #       context-sensitivity is important. for example, the following
    #       numpydoc would be unexpectedly invalid:
    #         Returns:
    #         --------
    #         value : ( number | "some ## weird ## string" )
    text = decomment(text, self.comment)
    nlines = text2numpylines(textwrap.dedent(text).strip())
    for ndoc, typ in self.parseNumpyMulti(nlines, eager=eager):
      yield numpylines2text(ndoc) or None, typ

  #----------------------------------------------------------------------------
  def parseNumpy(self, nlines, eager=False):
    ret = list(self.parseNumpyMulti(nlines, eager=eager))
    if not ret:
      return ret
    if len(ret) > 1:
      raise ValueError(
        'context does not support multi-types and/or interleaved text: %r'
        % (numpylines2text(nlines),))
    return ret[0]

  #----------------------------------------------------------------------------
  def parseNumpyMulti(self, nlines, eager=False):
    nlines = self.decommentNumpy(nlines)
    for ndoc, ntyp in self._parse(nlines, eager=eager):
      yield ndoc or None, ntyp

  #----------------------------------------------------------------------------
  def decommentNumpy(self, nlines):
    if self.comment:
      nlines = [
        (
          nline[0].split(self.comment)[0],
          nline[1],
          [sline.split(self.comment)[0] for sline in nline[2]],
        )
        for nline in nlines]
    return [
      (
        nline[0].strip(),
        nline[1].strip(),
        [sline.rstrip() for sline in nline[2]],
      )
      for nline in nlines]

  #----------------------------------------------------------------------------
  def _parse(self, nlines, eager=False):

    # print '>'*70
    # for nline in nlines:
    #   print 'LINE:',repr(nline)
    # print '<'*70

    curdoc = []
    for idx, nline in enumerate(nlines):
      name, spec, slines = nline
      # todo: this check for ``['', '']`` is due to FixedNumpyDoc behaviour...
      if slines == [''] or slines == ['', '']:
        slines = []
      if ( not name ) and spec:
        raise ValueError(
          'unexpected NumpyDoc spec-but-no-name line structure: %r'
          % (nline,))
      if not spec and not slines:
        # it's a simple documentation line, unless we are in eager
        # parsing, and it could be a standalone return type, but then
        # we require surrounding blank lines.
        # todo: these checks for ``['', '']`` is due to FixedNumpyDoc behaviour...
        if eager \
            and _could_be_a_type(name) \
            and ( idx == 0 or nlines[idx - 1][2][-2:] == ['', ''] ) \
            and ( idx == ( len(nlines) - 1 ) or nlines[idx][2] == ['', ''] ) \
          :
          yield curdoc, self._parseDef(name, '\n'.join(slines).strip())
          curdoc = []
          continue
        curdoc.append(nline)
        continue
      if spec:
        yield curdoc, self._parseKey(name, spec, '\n'.join(slines).strip())
        curdoc = []
        continue
      if _could_be_a_type(name):
        yield curdoc, self._parseDef(name, '\n'.join(slines).strip())
        curdoc = []
        continue
      curdoc.append(nline)
      continue
    if curdoc:
      yield curdoc, None

  #----------------------------------------------------------------------------
  def _parseKey(self, name, spec, text):
    ret = TypeRef(name=name)
    ret.type, ret.params = self.parseSpec(spec)
    if not text:
      return ret
    # todo: generalize this to handle anything (and any number of)
    #       compound types that could support sub-definition. see
    #       example in:
    #         test_parser:test_parse_list_with_multi_types
    if ret.type.is_list():
      sdoc, styp = self.parse(text)
      if sdoc:
        ret.doc = sdoc
      if styp:
        if ret.type.value:
          if styp.base == ret.type.value.base and styp.name == ret.type.value.name:
            ret.type.value = styp
          else:
            raise ValueError(
              'conflicting type definition for key %s: %r != %r'
              % (name, ret.type.value, styp))
        else:
          raise ValueError(
            'unexpected type definition for key %s: %r' % (name, text))
    else:
      sdoc, styp = self.parse(text)
      if styp:
        if styp.is_dict() and styp.name == Type.DICT \
            and not styp.doc and styp.value \
            and ret.type.is_dict() and not ret.type.value:
          ret.type.value = styp.value
          if ret.type.name != Type.DICT and not ret.type.doc and sdoc:
            # push the preamble into the type's documentation (not the
            # attribute), but only if it is a declared type. note that
            # this may later be undone, if necessary, during merge.
            ret.type.doc = sdoc
            sdoc = None
      if sdoc:
        ret.doc = sdoc
    return ret

  #----------------------------------------------------------------------------
  def _parseDef(self, name, text):
    ret, params = self.parseSpec(name)
    if params:
      raise ValueError(
        'top-level type parameters currently not supported: %r' % (name,))
    if not text:
      return ret
    doc, typ = self.parse(text)
    if doc:
      ret.doc = doc
    if typ:
      if typ.doc:
        if doc:
          raise ValueError(
            'conflicting preamble text and type info text: %r' % (text,))
        ret.doc = typ.doc
      if not ( typ.base == Type.COMPOUND and typ.name == Type.DICT ):
        raise ValueError(
          'invalid attributes specified for %s: %r' % (name, text))
      ret.value = typ.value
    return ret

  #----------------------------------------------------------------------------
  def parseSpec(self, spec):
    if not spec:
      return None, None
    if self.comment:
      spec = spec.split(self.comment, 1)[0]
    spec = spec.strip()
    if not spec:
      return None, None
    typ, par = self.parseType(spec, complete=False)
    if par:
      par = par.strip()
      if not par.startswith(','):
        raise ValueError('invalid type specification: %r' % (spec,))
      par = parseParams(par[1:])
    return (typ, par or None)

  #----------------------------------------------------------------------------
  def parseType(self, text, complete=True):
    # TODO: move typespec parsing from typereg to here...
    return _typereg.parseType(text, complete=complete)

#------------------------------------------------------------------------------
# end of $Id$
# $ChangeLog$
#------------------------------------------------------------------------------
