# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2013/09/09
# copy: (C) Copyright 2013 Cadit Health Inc., All Rights Reserved.
#------------------------------------------------------------------------------

from pyramid_controllers.util import getVersion
import asset

from .controller import DescribeController
from . import test_helpers

#------------------------------------------------------------------------------
class TestRender(test_helpers.TestHelper):

  #----------------------------------------------------------------------------
  def test_simple(self):
    from .test.render_simple import Root
    root = Root()
    root.desc = DescribeController(
      root, doc='URL tree description.',
      settings={
        'formats'         : 'rst',
        'index-redirect'  : 'false',
        'exclude'         : ('|^/desc(/.*)?$|'),
        'format.request'  : 'true',
      })
    self.assertResponse(
      self.send(root, '/desc?showLegend=false&rstMax=false&showMeta=false'), 200,
      self.loadTestData('render_simple.output.rst'))

  #----------------------------------------------------------------------------
  def test_template(self):
    from .test.render_simple import Root
    root = Root()
    root.desc = DescribeController(
      root, doc='URL tree description.',
      settings={
        'formats'         : 'rst',
        'index-redirect'  : 'false',
        'exclude'         : ('|^/desc(/.*)?$|'),
        'format.request'  : 'true',
        'render.template' : 'pyramid_describe:test/render_template.mako',
      })
    self.assertResponse(
      self.send(root, '/desc?showLegend=false&rstMax=false&showMeta=false'), 200,
      self.loadTestData('render_template.output.rst'))

  #----------------------------------------------------------------------------
  def test_template_withMetaAndMax(self):
    from .test.render_simple import Root
    root = Root()
    root.desc = DescribeController(
      root, doc='URL tree description.',
      settings={
        'formats'         : 'rst',
        'index-redirect'  : 'false',
        'exclude'         : ('|^/desc(/.*)?$|'),
        'format.request'  : 'true',
        'render.template' : 'pyramid_describe:test/render_template.mako',
      })
    self.assertResponse(
      self.send(root, '/desc?showLegend=false&rstMax=true&showMeta=true'), 200,
      self.loadTestData('render_template-withmetamax.output.rst', {
        'version' : getVersion('pyramid_describe'),
      }))

  #----------------------------------------------------------------------------
  def test_template_endpointList(self):
    from .test.render_simple import Root
    root = Root()
    root.desc = DescribeController(
      root, doc='URL tree description.',
      settings={
        'formats'         : 'rst',
        'index-redirect'  : 'false',
        'exclude'         : ('|^/desc(/.*)?$|'),
        'format.request'  : 'true',
        'render.template' : 'pyramid_describe:test/render_template_list.mako',
      })
    self.assertResponse(
      self.send(root, '/desc?showLegend=false&rstMax=false&showMeta=false'), 200,
      self.loadTestData('render_template_list.output.rst'))

  #----------------------------------------------------------------------------
  def test_typereg_base(self):
    from .test.render_typereg_base import Root
    root = Root()
    root.desc = DescribeController(
      root, doc='URL tree description.',
      settings={
        'formats'         : 'rst',
        'index-redirect'  : 'false',
        'exclude'         : ('|^/desc(/.*)?$|'),
        'format.request'  : 'true',
      })
    self.assertResponse(
      self.send(root, '/desc?showLegend=false&rstMax=false&showMeta=false'), 200,
      self.loadTestData('render_typereg_base.output.rst'))

  #----------------------------------------------------------------------------
  def test_typereg_types(self):
    from .test.render_typereg_types import Root
    root = Root()
    root.desc = DescribeController(
      root, doc='URL tree description.',
      settings={
        'formats'         : 'rst',
        'index-redirect'  : 'false',
        'exclude'         : ('|^/desc(/.*)?$|'),
        'format.request'  : 'true',
      })
    self.assertResponse(
      self.send(root, '/desc?showLegend=false&rstMax=false&showMeta=false'), 200,
      self.loadTestData('render_typereg_types.output.rst'))

  @staticmethod
  # todo: how to mark this as a "test" plugin, and therefore not
  #       auto-registerable?...
  @asset.plugin(
    'pyramid_describe.plugins.catalog.filters', 'test-filter')
  def filter_triangle(catalog, context):
    # TODO: THIS METHOD OF FILTERING TYPES HAS BEEN DEPRECATED!...
    #       USE `pyramid_describe.plugins.type.filters` PLUGINS INSTEAD.
    from .scope import Scope
    return Scope(
      catalog, types = [t for t in catalog.types if t.name != 'Triangle'])

  #----------------------------------------------------------------------------
  def test_typereg_types_filtered(self):
    from .test.render_typereg_types import Root
    root = Root()
    root.desc = DescribeController(
      root, doc='URL tree description.',
      settings={
        'formats'         : 'rst',
        'index-redirect'  : 'false',
        'exclude'         : ('|^/desc(/.*)?$|'),
        'format.request'  : 'true',
        'catalog.filters' : '+pyramid_describe.test_render.TestRender.filter_triangle',
      })
    self.assertResponse(
      self.send(root, '/desc?showLegend=false&rstMax=false&showMeta=false'), 200,
      self.loadTestData('render_typereg_types-filtered.output.rst'))

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
