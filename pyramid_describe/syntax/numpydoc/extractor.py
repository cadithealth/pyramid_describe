# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2016/01/05
# copy: (C) Copyright 2016-EOT Cadit Inc., All Rights Reserved.
#------------------------------------------------------------------------------

'''
This module extracts type information from a documentation string in a
NumpyDoc format.
'''

# TODO: this module is a mess. sorry. please don't judge me!

import re
import logging

from numpydoc.docscrape import NumpyDocString, Reader

from ...typereg import TypeRegistry, Type, TypeRef
from . import parser

#------------------------------------------------------------------------------

DEFAULT_COMMENT_TOKEN = TypeRegistry.DEFAULT_OPTIONS['commentToken']

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
def _could_be_a_token(context, value):
  # todo: currently it only supports something like:
  #         Person
  #       it would be nice to support something like this too:
  #         list(ref(Thing))
  #       ==> use the TypeManager to parse it and see if it resolves???
  #       ==> or, at the very minimum, parse the first token and see if
  #           it is in the TypeManager's scalars, aliases, or declared
  #           types...
  return bool(context.options.typereg.isType(value))

#------------------------------------------------------------------------------
def _split_numpy_doc_attr_lines(context, nlines, eager=False):
  # look for and record the first lines that have:
  attr   = None     # a key-value numpy pair
  decl   = None     # a type declaration with indented lines
  pdecl  = None     # a possible eager type declaration (no indented lines)
  for idx, (name, spec, lines) in enumerate(nlines):
    if attr is None and spec:
      attr = idx
      break
    if _could_be_a_token(context, name) and not spec:
      if lines and lines != ['']:
        if decl is None:
          decl = idx
      else:
        if pdecl is None:
          pdecl = idx
  if attr is not None:
    idx = attr
  elif decl is not None:
    idx = decl
  elif eager and pdecl is not None:
    idx = pdecl
  else:
    return (nlines, [])
  return (nlines[:idx], nlines[idx:])

#------------------------------------------------------------------------------
def _convert_numpy_lines(context, nlines, commentToken):
  if commentToken:
    # note: *NOT* de-commenting the spec (nline[1]) because that will
    #       be taken care of by parseType later on.
    nlines = [
      (
        nline[0].split(commentToken)[0],
        nline[1],
        [sline.split(commentToken)[0] for sline in nline[2]],
      )
      for nline in nlines]
  nlines = [
    (
      nline[0].strip(),
      nline[1].strip(),
      [sline.rstrip() for sline in nline[2]],
    )
    for nline in nlines]
  # first, check to make sure all attributes are the same style
  # (i.e. all key-value pairs or all keywords-only).
  base = (bool(nlines[0][0]), bool(nlines[0][1]))
  if base not in ((True, True), (True, False)):
    raise ValueError('unknown/unsupported numpydoc attribute declaration style')
  for name, spec, misc in nlines:
    if (bool(name), bool(spec)) != base:
      raise ValueError('inconsistent numpydoc attribute declaration style')
  result = []
  for name, spec, lines in nlines:
    cur = dict(spec=spec or name)
    if spec:
      cur.update(name=name)
    sub = '\n'.join(lines).strip()
    if sub:
      sub = extract(context, sub, commentToken, eager=False)

      if sub.get('doc'):
        # TODO: *** HACK ALERT ***
        #       basically, this is creating a temporary workaround
        #       for list-with-schema specs that DON'T have non-schema
        #       documentation, eg unit test
        #         test_extract_list_with_schema_and_no_attribute_comments
        #       NOTE that as a consequence 
#        if not cur.get('spec', '').startswith('list('):
          cur['doc'] = sub.pop('doc')
        # /TODO

      # if sub.get('doc') and list(sub.keys()) == ['doc']:
      #   cur['doc'] = sub.pop('doc')

      if sub.get('spec') == 'dict' \
          and 'name' not in sub \
          and cur.get('spec') not in ('oneof', 'list'):
        sub.pop('spec')
        cur.update(sub)
        sub = None
      if sub:
        cur['value'] = [sub]
    result.append(cur)
  if base == (True, True):
    return dict(spec='dict', value=result)
  if len(result) == 1:
    return result[0]
  return dict(spec='oneof', value=result)

#------------------------------------------------------------------------------
def _crunchType(typ, **kw):
  # todo: this should also collapse neighboring 'oneof's...
  #       anything else?
  if not kw:
    if isinstance(typ, Type) \
        and typ.base == Type.COMPOUND and typ.name == Type.ONEOF \
        and not typ.doc and len(typ.value) == 1:
      return _crunchType(typ.value[0])
    return typ
  kw = {key: value for key, value in kw.items() if value is not None}
  if not isinstance(typ, TypeRef):
    return TypeRef(type=typ, **kw)
  for key, value in kw.items():
    cur = getattr(typ, key, None)
    if cur is not None and cur != value:
      raise ValueError('TypeRef %r attribute collision' % (key,))
    setattr(typ, key, value)
  return typ

#------------------------------------------------------------------------------
def _convert_type(context, ityp):
  # TODO: make `extractor.py` do this...

  if not ityp:
    return None

  name  = ityp.get('name')
  spec  = ityp.get('spec')
  doc   = ityp.get('doc')
  value = ityp.get('value')

  rtyp, rpar  = parser.parseSpec(context, spec)

  if not ( name or doc or value ):
    if rpar:
      return _crunchType(rtyp, params=rpar)
    return _crunchType(rtyp)

  if rtyp.base == Type.DICT \
      or ( rtyp.base == Type.COMPOUND \
           and rtyp.name in (Type.DICT, Type.ONEOF, Type.UNION) ):
    if value:
      rtyp.value = [_convert_type(context, sub) for sub in value]
      value = None
    elif doc:
      rtyp = TypeRef(type=rtyp)
    if doc:
      rtyp.doc = doc
      doc = None

  elif rtyp.base == Type.COMPOUND and rtyp.name in (Type.LIST,):
    # todo: special casing ``list(Schema)`` here... genericize so that
    #       any combination of compound-type works, eg.
    #       ``list(OneSchema | TwoSchema)`` (and then specifying the
    #       structure for either or all, etc...

    if value:
      value = [_convert_type(context, sub) for sub in value]
      if len(value) != 1:
        raise ValueError(
          'list(...) currently only supports a single inline schema')

      styp = value[0]

      # # TODO: *** HACK ALERT ***
      # #       this is horrible... basically, this is undoing the
      # #       artificial "oneof" that was added for dual-documentation
      # #       in `_convert_numpy_lines`, and is to pass the unit test
      # #         test_extract_list_with_schema_and_attribute_comments
      # #       ...
      # #       ==> this *should* be addressed when `convert` is
      # #           adjusted to:
      # #             a) convert to typereg objects on the fly
      # #             b) always return (preamble, types) tuples
      # if styp.base == Type.COMPOUND and styp.name == Type.ONEOF \
      #     and styp.doc and styp.value and len(styp.value) == 1 \
      #     and styp.value[0].base == rtyp.value.base \
      #     and styp.value[0].name == rtyp.value.name:
      #   if doc:
      #     raise ValueError(
      #       'bubbling up of documentation collision for: %r into %r'
      #       % (styp.doc, doc))
      #   rtyp.doc = styp.doc
      #   styp = styp.value[0]
      # # /TODO

      if not rtyp.value \
          or rtyp.value.base != styp.base \
          or rtyp.value.name != styp.name:
        raise ValueError(
          'list(...) inline schema mismatch: %r != %r'
          % (rtyp.value, styp))
      rtyp.value = styp
      value = None

  else:
    # numpydoc does not support specifying details of any other kind of type...
    if value:
      raise ValueError(
        'unexpected complex value with non-dict base type: %r'
        % (value,))
    return _crunchType(rtyp, name=name, doc=doc, params=rpar)

  if not ( name or doc or rpar ):
    return _crunchType(rtyp)
  return _crunchType(rtyp, name=name, doc=doc, params=rpar)

#------------------------------------------------------------------------------
def _numpy2type(context, nlines, commentToken, numpyret=True, eager=True):

  # print '>>'*20
  # for line in nlines:
  #   print 'LINE:',repr(line)
  # print '--'*20


  preamble, attrs = _split_numpy_doc_attr_lines(context, nlines, eager=eager)

  # print 'PRE:',repr(preamble)
  # for line in attrs:
  #   print '   A:',repr(line)
  # print '<<'*20



  if not attrs:
    return None
  if not numpyret:
    preamble = _numpylines2text(preamble)
  typ = _convert_numpy_lines(context, attrs, commentToken) or None

  # print 'TYPRET:',repr(typ)

  # if typ and typ.get('doc') == '@PUBLIC':
  #   import pdb;pdb.set_trace()

  return (preamble, typ)

#------------------------------------------------------------------------------
def numpy2type(context, nlines, numpyret=True, eager=True):
  '''
  Converts the NumpyDoc-parsed lines `nlines` to a tuple of preamble
  text and a type specification object.

  If no type specification object could be extracted, this returns
  ``None``.

  If `numpyret` is truthy, the returned preamble text will be a
  NumpyDoc-parsed lines structure.

  If `eager` is truthy, text will be eagerly transformed to a
  specification object, even when this would be debatable. For
  example, the following will extract a type declaration of `Shape`
  (with an empty preamble) if this is called with `nlines` set to the
  `Returns` section of::

    Returns
    -------

    Person
  '''
  ret = _numpy2type(
    context, nlines, context.options.commentToken,
    numpyret=numpyret, eager=eager)
  if not ret or not ret[1]:
    return ret
  # TODO: make `typ` be a typereg.Type or typereg.TypeRef during
  #       parsing, rather than re-converting here!...
  return (ret[0], _convert_type(context, ret[1]))

#------------------------------------------------------------------------------
def extract(context, text, commentToken=DEFAULT_COMMENT_TOKEN, eager=False):
  '''
  @DEPRECATED

  NOTE: Use `extractType` instead!

  Extracts a list of attribute specification objects from `text`,
  given in numpydoc-style attribute declaration format.

  Format:

    [OPTIONAL-PRELUDE]

    {ATTRIBUTE-DECLARATION}
    ...

  Example::

    This is a single-alternative (implicit) top-level anonymous
    "shape" declaration.

    name : str
    sides : int

  Example::

    This is a single-alternative (explicit) top-level anonymous
    "shape" declaration.

    dict
      name : str
      sides : int

  Example::

    This is a single-alternative top-level declarative type 'Shape'.

    Shape
      name : str
      sides : int

  Example::

    This is a single-alternative namespaced anonymous "shape"
    declaration.

    shape : dict
      name : str
      sides : int

  Example::

    This is a single-alternative namespaced declarative type 'Shape'.

    shape : Shape
      name : str
      sides : int

  Example::

    This is a dual-alternative top-level declarative type 'Shape' or
    type 'Address':

    Shape
      name : str
      sides : int

    Address
      lines : list(str)
      region : str
      locality : str
      pocode : str


  Returns
  =======

  AttributeDescription

    Returns an attribute decscription dict that can have the following
    possible attributes:

    doc : str, optional, default: null

      Documentation for the attribute.

    name : str, optional, default: null

      If named, the name of the attribute.

    spec : str, optional, default: null

      If type details are provided, the type specification.

    value : list, optional, default: null

      For `spec=oneof` types, a list of possible alternatives.
      For `spec=union` types, a list of required types.
      For `spec=dict` (and custom) types, a list of AttributeDescription's.
      For `spec=list` types, an AttributeDescription.

  '''

  # todo: this is pretty horrible... but basically i'm "probing" the
  #       text to determine where the prelude ends...
  # todo: what if there is more advanced rST in `text`?...

  ndoc = _text2numpylines(text)
  res  = _numpy2type(context, ndoc, commentToken, eager=eager, numpyret=False)
  if not res:
    return dict(doc=text)
  doc, typ = res
  if not typ:
    if not doc:
      raise ValueError('could not extract numpy attributes from %r' % (text,))
    return dict(doc=doc)
  if doc:
    if not typ.get('doc', '').strip():
      typ['doc'] = doc
    else:
      typ = dict(spec='oneof', doc=doc, value=[typ])
  return typ

#------------------------------------------------------------------------------
def extractType(context, text, commentToken=DEFAULT_COMMENT_TOKEN, eager=False):
  typ = extract(context, text, commentToken=commentToken, eager=eager)
  return _convert_type(context, typ)

#------------------------------------------------------------------------------
# TODO: everything below here (and some above) is a **HACK**! ugh.
#------------------------------------------------------------------------------

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
def extractMultiType(context, text, commentToken=DEFAULT_COMMENT_TOKEN, eager=False):
  '''
  Similar to :func:`extract`, but returns a generator of two-element
  tuples of ( documentation, `typereg.Type` ).

  Also, unlike `extract`, this call supports mixing of declaration
  styles (i.e. mixing of Type declarations and TypeRef declarations),
  but TypeRef declarations are converted into Type.EXTENSION types.
  '''
  nlines = list(_text2numpylines(decomment(text, commentToken)))
  prev   = 0
  for idx, (name, spec, lines) in enumerate(nlines):
    if not spec and lines == ['']:
      continue
    doc, typ = numpy2type(
      context, nlines[prev:idx + 1], eager=eager, numpyret=False)
    # "unwrap" anonymous dicts
    if typ and typ.base == Type.COMPOUND and typ.name == Type.DICT:
      if len(list(typ.children)) != 1:
        raise ValueError(
          'internal error -- unexpected multi-attribute in anonymous dict: %r'
          % (typ,))
      typ = list(typ.children)[0]
    # convert TypeRef's into extension types
    if isinstance(typ, TypeRef):
      typ = Type(base=Type.EXTENSION, name=typ.name, doc=typ.doc,
                 value=TypeRef(params=typ.params, type=typ.type))
    yield (doc or None, typ)
    prev = idx + 1

#------------------------------------------------------------------------------
# end of $Id$
# $ChangeLog$
#------------------------------------------------------------------------------
