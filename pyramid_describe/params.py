# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2016/01/10
# copy: (C) Copyright 2016-EOT Cadit Inc., All Rights Reserved.
#------------------------------------------------------------------------------

import logging
import json

import morph

# TODO: handle encoding & decoding of commas in param values...
# todo: i18n?...

#------------------------------------------------------------------------------

log = logging.getLogger(__name__)

ACCESS_C                = 'create'
ACCESS_R                = 'read'
ACCESS_W                = 'write'
ACCESS_ALL              = [ACCESS_C, ACCESS_R, ACCESS_W]

ATTR_CREATE             = ACCESS_C
ATTR_READ               = ACCESS_R
ATTR_WRITE              = ACCESS_W
ATTR_REQUIRED           = 'required'
ATTR_OPTIONAL           = 'optional'
ATTR_DEFAULT            = 'default'
ATTR_DEFAULT_TO         = 'default_to'
ATTR_NULLABLE           = 'nullable'
ATTR_CLASS              = 'class'

# note: these are not ATTR_* because they are aliases only (and should
# always be auto-converted to their respective attributes)
QUAL_UPDATE             = 'update'
QUAL_UPDATE_ONLY        = 'update-only'
QUAL_CREATE_ONLY        = 'create-only'
QUAL_READ_ONLY          = 'read-only'
QUAL_WRITE_ONLY         = 'write-only'
QUAL_READ_WRITE         = 'read-write'

#------------------------------------------------------------------------------
def paramValueEncode(value):
  sval = str(value)
  if value == paramValueDecode(sval):
    return sval
  return json.dumps(value)

#------------------------------------------------------------------------------
def paramValueDecode(text):
  try:
    return json.loads(text)
  except Exception:
    return text

#------------------------------------------------------------------------------
def q2a(name):
  '''
  Converts a qualifier name to an attribute name,
  e.g. ``default-to`` => ``default_to``.
  '''
  return name.replace('-', '_')

#------------------------------------------------------------------------------
def a2q(name):
  '''Inverse of `q2a`.'''
  return name.replace('_', '-')

#------------------------------------------------------------------------------
def prepare(params, exclude_params=(ATTR_CLASS,)):
  '''
  Generates (key, value) pairs for all parameters defined in `type`
  adjusted for relevance, redundancy, and ordering for the context
  of type documentation. The `value` will always be stringified,
  except if the `key` is a flag, then `value` will be ``None``.

  The following rules are applied:

  * access control parameters (read/write/create) come first

  * 'optional' and 'nullable' are removed if they can be inferred
    (e.g. there is a default that is set to null)

  * parameters listed in `exclude_params` are squelched

  * `required` overrides and is merged into `optional`

  * defaults come last

  * examples come last or before defaults
  '''

  # todo: some ideas on improvements:
  #       - param defaults (may) depend on type
  #       - use more powerful param mapping technology

  # todo: apply `expose` rules...
  #   expose = spec.get('expose', [])
  #   for key in sorted(spec.params.keys()):
  #     if key in RST_PARAMS:
  #       continue
  #     if key not in expose and not key.startswith('@'):
  #       log.debug('ignoring armorspec parameter %r', key)
  #       continue

  params = dict(params or {})
  if ATTR_REQUIRED in params:
    params[ATTR_OPTIONAL] = not params.pop(ATTR_REQUIRED)
  if not params.get(ATTR_OPTIONAL):
    params.pop(ATTR_OPTIONAL, None)
  if ATTR_DEFAULT in params or ATTR_DEFAULT_TO in params:
    params.pop(ATTR_OPTIONAL, None)
  if ATTR_DEFAULT in params and params[ATTR_DEFAULT] is None:
    params.pop(ATTR_NULLABLE, None)

  if not params:
    return

  mode = ( 'r' if params.get(ATTR_READ,   False) else '' ) \
    +    ( 'w' if params.get(ATTR_WRITE,  False) else '' ) \
    +    ( 'c' if params.get(ATTR_CREATE, False) else '' )
  accessMap = {
    'rwc' : [],
    'rw'  : [a2q(ATTR_READ), a2q(ATTR_WRITE)],    # todo: warn nonsense since no `create`?
    'rc'  : [a2q(ATTR_READ), a2q(ATTR_CREATE)],
    'r'   : [QUAL_READ_ONLY],
    'wc'  : [QUAL_WRITE_ONLY],
    'w'   : [QUAL_WRITE_ONLY],       # todo: warn nonsense since no `create`?
    'c'   : [QUAL_CREATE_ONLY],
    ''    : [],                   # todo: warn nonsense since nothing?
  }
  for sym in accessMap[mode]:
    yield sym, None
  for key in sorted(params.keys()):
    if key in (ATTR_DEFAULT, ATTR_DEFAULT_TO, ATTR_READ, ATTR_WRITE, ATTR_CREATE):
      continue
    if exclude_params and key in exclude_params:
      continue
    val = params.get(key)
    key = a2q(key)
    if val is True:
      yield key, None
    else:
      yield key, paramValueEncode(val)
  if ATTR_DEFAULT_TO in params:
    yield a2q(ATTR_DEFAULT_TO), str(params[ATTR_DEFAULT_TO])
  if ATTR_DEFAULT in params:
    yield a2q(ATTR_DEFAULT), json.dumps(params[ATTR_DEFAULT])

#------------------------------------------------------------------------------
def render(params, *args, **kw):
  ret = []
  for key, value in prepare(params, *args, **kw):
    if value is None:
      ret.append(key)
    else:
      ret.append(key + ': ' + value)
  return ', '.join(ret)

#------------------------------------------------------------------------------
def parse(spec):
  '''
  Parses the parameters specified in `spec` and returns a dictionary
  of normalized key/value pairs.
  '''
  # TODO: uh... juice this!
  #         - use a lexer to parse the line!
  #         - use more powerful param mapping technology...
  #         - param defaults should depend on type, mode, and channel!!..
  parts  = [part.strip() for part in spec.split(',')]
  ret    = dict()
  for part in parts:
    key = part
    if ':' in part:
      key, val = [x.strip() for x in part.split(':', 1)]
    elif '=' in part:
      key, val = [x.strip() for x in part.split('=', 1)]
    else:
      val = True
    okey = key
    key  = q2a(key)
    if okey == ATTR_DEFAULT:
      try:
        val = json.loads(val)
      except ValueError:
        log.warning(
          'non-JSON default value in armor spec: %r (moved to "%s")',
          spec, a2q(ATTR_DEFAULT_TO))
        key = ATTR_DEFAULT_TO
    else:
      val = paramValueDecode(val)
    if key in ret and val != ret[key]:
      raise ValueError(
        'qualifier "%s" collision (%r != %r)' % (okey, ret[key], val))
    ret[key] = val
  return normParams(ret)

#------------------------------------------------------------------------------
def tobool(val):
  if val in (True, False):
    return val
  try:
    val = json.loads(val)
    if val in (True, False):
      return val
  except:
    pass
  raise ValueError('%r is not a boolean')

#------------------------------------------------------------------------------
def normParams(params):

  if not params:
    return None

  params = dict(params)

  # todo: i18n?...
  paramAliases = {
    ATTR_READ             : ['r'],
    q2a(QUAL_READ_ONLY)   : ['ro'],
    ATTR_WRITE            : ['w', 'u', q2a(QUAL_UPDATE)],
    q2a(QUAL_WRITE_ONLY)  : ['wo', 'uo', q2a(QUAL_UPDATE_ONLY)],
    ATTR_CREATE           : ['c'],
    q2a(QUAL_CREATE_ONLY) : ['co'],
    q2a(QUAL_READ_WRITE)  : ['rw'],
  }
  paramMap = {
    q2a(QUAL_READ_ONLY)   : {ATTR_READ: True,  ATTR_WRITE: False, ATTR_CREATE: False},
    q2a(QUAL_WRITE_ONLY)  : {ATTR_READ: False, ATTR_WRITE: True,  ATTR_CREATE: True },
    q2a(QUAL_CREATE_ONLY) : {ATTR_READ: False, ATTR_WRITE: False, ATTR_CREATE: True },
    q2a(QUAL_READ_WRITE)  : {ATTR_READ: True,  ATTR_WRITE: True,  ATTR_CREATE: True },
    ATTR_REQUIRED         : {ATTR_OPTIONAL: False},
  }

  for key in paramAliases.keys():
    if key in params:
      try:
        params[key] = tobool(params[key])
      except Exception as err:
        raise ValueError('invalid value for qualifier %r: %s' % (key, err))

  for key, aliases in paramAliases.items():
    for alias in aliases:
      if alias in params:
        try:
          params[alias] = tobool(params[alias])
        except Exception as err:
          raise ValueError('invalid value for qualifier %r: %s' % (alias, err))
        if key in params and params[key] != params[alias]:
          raise ValueError('conflicting values for qualifier %r' % (key,))
        params[key] = params.pop(alias)

  for key, values in paramMap.items():
    if key not in params:
      continue
    if not params[key]:
      raise ValueError('qualifier %r must be true or not specified' % (key,))
    for vkey, vval in values.items():
      if vkey in params and params[vkey] != vval:
        raise ValueError(
          'conflicting values for qualifier %r and %r' % (key, vkey))
      params[vkey] = vval
    params.pop(key)

  if ACCESS_W in params and ACCESS_C not in params:
    params[ACCESS_C] = params[ACCESS_W]

  if ATTR_DEFAULT in params or ATTR_DEFAULT_TO in params:
    if ATTR_OPTIONAL in params and not params[ATTR_OPTIONAL]:
      raise ValueError('conflicting qualifiers: required vs. default value')
    params[ATTR_OPTIONAL] = True

  return params

#------------------------------------------------------------------------------
# end of $Id$
# $ChangeLog$
#------------------------------------------------------------------------------
