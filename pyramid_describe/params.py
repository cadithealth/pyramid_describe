# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2016/01/10
# copy: (C) Copyright 2016-EOT Cadit Inc., All Rights Reserved.
#------------------------------------------------------------------------------

import logging
import json

# TODO: handle encoding & decoding of commas in param values...

#------------------------------------------------------------------------------

log = logging.getLogger(__name__)

ACCESS_C                = 'create'
ACCESS_R                = 'read'
ACCESS_W                = 'write'
ACCESS_ALL              = [ACCESS_C, ACCESS_R, ACCESS_W]

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
def prepare(params, exclude_params=('class',)):
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
  if 'required' in params:
    params['optional'] = not params.pop('required')
  if not params.get('optional'):
    params.pop('optional', None)
  if 'default' in params or 'default_to' in params:
    params.pop('optional', None)
  if 'default' in params and params['default'] is None:
    params.pop('nullable', None)

  if not params:
    return

  mode = ( 'r' if 'read' in params else '' ) \
    + ( 'w' if 'write' in params else '' ) \
    + ( 'c' if 'create' in params else '' )
  accessMap = {
    'rwc' : [],
    'rw'  : ['read', 'write'],    # todo: warn nonsense since no `create`?
    'rc'  : ['read', 'create'],
    'r'   : ['read-only'],
    'wc'  : ['write-only'],
    'w'   : ['write-only'],       # todo: warn nonsense since no `create`?
    'c'   : ['create-only'],
    ''    : [],                   # todo: warn nonsense since nothing?
  }
  for sym in accessMap[mode]:
    yield sym, None
  for key in sorted(params.keys()):
    if key in ('default', 'default_to', 'read', 'write', 'create'):
      continue
    if exclude_params and key in exclude_params:
      continue
    val = params.get(key)
    key = key.replace('_', '-')
    if val is True:
      yield key, None
    else:
      yield key, paramValueEncode(val)
  if 'default_to' in params:
    yield 'default-to', str(params['default_to'])
  if 'default' in params:
    yield 'default', json.dumps(params['default'])

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
    key = key.replace('-', '_')
    if key == 'default':
      try:
        val = json.loads(val)
      except ValueError:
        log.warning(
          'non-JSON default value in armor spec: %r (moved to "default-to")',
          spec)
        key = 'default_to'
    else:
      val = paramValueDecode(val)
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
    ACCESS_R      : ['r'],
    'read_only'   : ['ro'],
    ACCESS_W      : ['w', 'u', 'update'],
    'write_only'  : ['wo', 'uo', 'update_only'],
    ACCESS_C      : ['c'],
    'create_only' : ['co'],
    'read_write'  : ['rw'],
  }
  paramMap = {
    'read_only'   : {ACCESS_R: True,  ACCESS_W: False, ACCESS_C: False},
    'write_only'  : {ACCESS_R: False, ACCESS_W: True,  ACCESS_C: True },
    'create_only' : {ACCESS_R: False, ACCESS_W: False, ACCESS_C: True },
    'read_write'  : {ACCESS_R: True,  ACCESS_W: True,  ACCESS_C: True },
    'required'    : {'optional': False},
  }

  for key in paramAliases.keys():
    if key in params:
      try:
        params[key] = tobool(params[key])
      except Exception as err:
        raise ValueError('invalid value for parameter %r: %s' % (key, err))

  for key, aliases in paramAliases.items():
    for alias in aliases:
      if alias in params:
        try:
          params[alias] = tobool(params[alias])
        except Exception as err:
          raise ValueError('invalid value for parameter %r: %s' % (alias, err))
        if key in params and params[key] != params[alias]:
          raise ValueError('conflicting values for parameter %r' % (key,))
        params[key] = params.pop(alias)

  for key, values in paramMap.items():
    if key not in params:
      continue
    if not params[key]:
      raise ValueError('parameter %r must be true or not specified' % (key,))
    for vkey, vval in values.items():
      if vkey in params and params[vkey] != vval:
        raise ValueError(
          'conflicting values for parameter %r and %r' % (key, vkey))
      params[vkey] = vval
    params.pop(key)

  if ACCESS_W in params and ACCESS_C not in params:
    params[ACCESS_C] = params[ACCESS_W]

  if 'default' in params or 'default_to' in params:
    if 'optional' in params and not params['optional']:
      raise ValueError('conflicting "optional" state with default value')
    params['optional'] = True

  return params

#------------------------------------------------------------------------------
# end of $Id$
# $ChangeLog$
#------------------------------------------------------------------------------
