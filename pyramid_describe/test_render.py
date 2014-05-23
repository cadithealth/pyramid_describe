# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2013/09/09
# copy: (C) Copyright 2013 Cadit Health Inc., All Rights Reserved.
#------------------------------------------------------------------------------

from pyramid_controllers.util import getVersion

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

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
