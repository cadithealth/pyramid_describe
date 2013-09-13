# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2013/09/09
# copy: (C) Copyright 2013 Cadit Health Inc., All Rights Reserved.
#------------------------------------------------------------------------------

from pyramid.settings import asbool, aslist
from .controller import DescribeController
from .util import pick

OPTION_PREFIXES_NAME    = 'describe.prefixes'
OPTION_PREFIXES_DEFAULT = 'describe'

def includeme(config):
  '''
  Includes pyramid-describe functionality into the pyramid application
  specified by `config`. See the main documentation for accepted
  configurations.
  '''
  config.include('pyramid_controllers')
  settings = config.registry.settings
  prefixes = aslist(settings.get(OPTION_PREFIXES_NAME, OPTION_PREFIXES_DEFAULT))
  for idx, prefix in enumerate(prefixes):
    curset = pick(settings, prefix=prefix + '.')
    curset['config'] = config
    controller = DescribeController(settings=curset)
    config.add_controller(
      curset.get('name', 'DescribeController-' + str(idx + 1)),
      curset.get('attach', '/describe'),
      controller)

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
