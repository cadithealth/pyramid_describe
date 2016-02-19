# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2016/02/19
# copy: (C) Copyright 2016-EOT Cadit Inc., All Rights Reserved.
#------------------------------------------------------------------------------

import re
import json

import yaml

#------------------------------------------------------------------------------

hex_cre         = re.compile(r'([a-f0-9][a-f0-9])+', re.IGNORECASE)

#------------------------------------------------------------------------------
def parseMulti(value, sep):
  ret = []
  rem = value
  while True:
    cur, rem = parsePartial(rem)
    ret.append(cur)
    if not rem or not rem.strip():
      return ret
    rem = rem.lstrip()
    if not rem.startswith(sep):
      raise ValueError(
        'dangling content %r in multi-constant: %r' % (rem, value))
    rem = rem[len(sep) : ].lstrip()
    if not rem:
      raise ValueError(
        'dangling separator %r in multi-constant: %r' % (sep, value))

#------------------------------------------------------------------------------
def parse(value, entirety=True):
  '''
  Attempts to parse the string `value` as a constant (e.g. a number,
  string, boolean, null, list, dict, etc). If `entirety` is truthy
  (the default), then the constant is returned IFF the entire `value`
  parsed into a single constant. If `entirety` is falsy, then the
  return value is a tuple of (constant, remainder), where `remainder`
  is whatever couldn't be parsed, IFF some portion of `value` could be
  parsed into a constant.
  '''
  ret, rem = parsePartial(value)
  if rem:
    rem = rem.lstrip()
  if entirety:
    if rem:
      raise ValueError(
        'invalid constant %r at position %i: %r'
        % (value, len(value) - len(rem), rem))
    return ret
  return ( ret, rem )

#------------------------------------------------------------------------------
def parsePartial(value):
  '''
  Same as :func:`parse`, but with `entirety` set to false.
  '''
  if not value or not value.strip():
    raise ValueError('invalid constant: %r' % (value,))
  value = value.lstrip()
  if value.startswith('0x'):
    return _hex(value)
  if value[0] in '01234567890-':
    return _num(value)
  if value[0] in '\'"{[':
    return _yaml(value)
  return _json(value)

#------------------------------------------------------------------------------
def _hex(value):
  if not value.startswith('0x'):
    raise ValueError('invalid constant (tried hex): %r' % (value,))
  match = hex_cre.match(value[2:])
  if not match:
    raise ValueError('invalid constant (tried hex): %r' % (value,))
  data = match.group(0)
  return ( data.decode('hex'), value[2 + len(data):] )

#------------------------------------------------------------------------------
def _num(value):
  # NOTE: using json, not yaml, because yaml is far too lenient.
  # for example ``78 !foo~`` would be interpreted as the entire
  # *string* "78 !foo~", not the number 78 + plus extra stuff...
  return _json(value)

#------------------------------------------------------------------------------
def _json(value):
  try:
    return ( json.loads(value), '' )
  except ValueError as exc:
    if not str(exc).startswith('Extra data: line 1 column '):
      raise
    idx = int(str(exc).split()[5]) - 1
    return ( json.loads(value[:idx]), value[idx:] )

#------------------------------------------------------------------------------
_yaml_error_cre = re.compile(
  r'^  in "<string>", line 1, column (\d+):$', flags=re.MULTILINE)
def _yaml(value):
  try:
    return ( yaml.load(value), '' )
  except (yaml.parser.ParserError, yaml.parser.ScannerError) as exc:
    idxs = [
      val for val in [
        int(m.group(1)) - 1
        for m in _yaml_error_cre.finditer(str(exc))]
      if val > 0]
    if not idxs:
      raise ValueError('invalid constant (tried yaml): %r' % (value,))
    for idx in reversed(sorted(idxs)):
      try:
        return ( yaml.load(value[:idx]), value[idx:] )
      except Exception as exc:
        continue
    raise ValueError('invalid constant (tried yaml): %r' % (value,))

#------------------------------------------------------------------------------
# end of $Id$
# $ChangeLog$
#------------------------------------------------------------------------------
