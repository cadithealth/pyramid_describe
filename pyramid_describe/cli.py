# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2013/09/09
# copy: (C) Copyright 2013 Cadit Health Inc., All Rights Reserved.
#------------------------------------------------------------------------------

import sys, argparse, six
import pyramid_iniherit.install
from pyramid.request import Request
from pyramid.paster import bootstrap

from .describer import FORMATS
from .i18n import _

#------------------------------------------------------------------------------
def describe_from_config(config, output, root=None, format=None, settings=None):
  env = bootstrap(config)
  context = dict(request=env['request'])
  return describe_from_app(
    env['app'], output, context=context, root=root, format=format, settings=settings)

#------------------------------------------------------------------------------
def describe_from_app(app, output, root=None, format=None, settings=None, context=None):

  # todo: is this necessary?
  root = root or '/'

  from pyramid.scripts.pviews import PViewsCommand
  pvcomm = PViewsCommand([])
  view = pvcomm._find_view(root, app.registry)
  from .describer import Describer
  desc = Describer(settings=settings)
  res = desc.describe(view, context=context, format=format, root=root).content
  if isinstance(res, six.string_types):
    # todo: encoding the PDF output to UTF-8 is generating the follow error:
    #         UnicodeDecodeError: 'ascii' codec can't decode byte 0xfe in
    #           position 28: ordinal not in range(128)
    #       that makes no sense... right? i mean, it says *ENcode*!...
    try:
      res = res.encode('UTF-8')
    except UnicodeDecodeError: pass
  output.write(res)

#------------------------------------------------------------------------------
def main(argv=None):

  cli = argparse.ArgumentParser(
    description = _('Describe a pyramid application URL hierarchy.')
    )

  cli.add_argument(
    _('-v'), _('--verbose'),
    dest='verbose', action='count', default=0,
    help=_('increase verbosity (can be specified multiple times)'))

  cli.add_argument(
    _('-s'), _('--setting'), metavar=_('KEY=VALUE'),
    dest='settings', action='append', default=[],
    help=_('add a Describer setting formatted as "KEY=VALUE", e.g.'
           ' ``--setting format.default=rst``'))

  cli.add_argument(
    _('-f'), _('--format'), metavar=_('FORMAT'),
    dest='format', action='store', choices=FORMATS,
    help=_('specify the output format to be generated'))

  cli.add_argument(
    _('-T'), _('--txt'),
    dest='format', action='store_const', const='txt',
    help=_('output a text-based tree hierarchy ("--format txt")'))

  if 'pdf' in FORMATS:
    cli.add_argument(
      _('-P'), _('--pdf'),
      dest='format', action='store_const', const='pdf',
      help=_('output a PDF document ("--format pdf")'))

  cli.add_argument(
    _('-R'), _('--rst'),
    dest='format', action='store_const', const='rst',
    help=_('output a reStructuredText document ("--format rst")'))

  cli.add_argument(
    _('-H'), _('--html'),
    dest='format', action='store_const', const='html',
    help=_('output an HTML document ("--format html")'))

  if 'yaml' in FORMATS:
    cli.add_argument(
      _('-Y'), _('--yaml'),
      dest='format', action='store_const', const='yaml',
      help=_('output a YAML document ("--format yaml")'))

  cli.add_argument(
    _('-J'), _('--json'),
    dest='format', action='store_const', const='json',
    help=_('output a JSON document ("--format json")'))

  cli.add_argument(
    _('-W'), _('--wadl'),
    dest='format', action='store_const', const='wadl',
    help=_('output a WADL document ("--format wadl")'))

  cli.add_argument(
    _('-X'), _('--xml'),
    dest='format', action='store_const', const='xml',
    help=_('output an XML document ("--format xml")'))

  cli.add_argument(
    'config', metavar=_('CONFIG'),
    help=_('PasteDeploy configuration file in "FILENAME#APPNAME" format,'
           ' where "#APPNAME" can be omitted and will default to "#main"'))

  cli.add_argument(
    'url', metavar=_('ROOT-URL'),
    nargs='?', default=None,
    help=_('host-relative URL to begin inspection at, i.e. all routes that'
           ' match this URL (and below) will be inspected; if omitted, will'
           ' default to "%(default)s"'))

  options = cli.parse_args(argv)

  try:
    options.settings = dict([val.split('=', 1) for val in options.settings])
  except Exception:
    cli.error('the setting "%r" is invalid - it must be specified'
              ' exactly as "KEY=VALUE"' % (options.settings,))

  describe_from_config(
    options.config, sys.stdout, root=options.url, format=options.format,
    settings=options.settings)

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
