# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2013/09/09
# copy: (C) Copyright 2013 Cadit Health Inc., All Rights Reserved.
#------------------------------------------------------------------------------

from pyramid.settings import asbool, aslist
from .controller import DescribeController
from .util import pick, resolve

GLOBAL_PREFIX           = 'describe'
OPTION_PREFIXES_NAME    = GLOBAL_PREFIX + '.prefixes'
OPTION_PREFIXES_DEFAULT = 'describe'
OPTION_CLASS_NAME       = GLOBAL_PREFIX + '.class'
OPTION_CLASS_DEFAULT    = DescribeController

def includeme(config):
  '''
  Includes pyramid-describe functionality into the pyramid application
  specified by `config`. See the main documentation for accepted
  configurations.
  '''
  config.include('pyramid_controllers')
  settings = config.registry.settings
  defkls   = resolve(settings.get(OPTION_CLASS_NAME, OPTION_CLASS_DEFAULT))
  prefixes = aslist(settings.get(OPTION_PREFIXES_NAME, OPTION_PREFIXES_DEFAULT))
  for idx, prefix in enumerate(prefixes):
    curset = pick(settings, prefix=prefix + '.')
    curset['config'] = config
    curkls = resolve(curset.get('class', defkls))
    controller = curkls(settings=curset)
    config.add_controller(
      curset.get('name', 'DescribeController-' + str(idx + 1)),
      curset.get('attach', '/describe'),
      controller)

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
