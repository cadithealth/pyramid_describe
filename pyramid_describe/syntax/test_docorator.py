# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2014/05/08
# copy: (C) Copyright 2014-EOT Cadit Inc., All Rights Reserved.
#------------------------------------------------------------------------------

from pyramid_controllers.util import getVersion

from ..controller import DescribeController
from ..util import adict
from .. import test_helpers
from . import docorator

#------------------------------------------------------------------------------
class TestDocorator(test_helpers.TestHelper):

  #----------------------------------------------------------------------------
  def test_firstLine(self):
    entry = adict(
      doc = '''\
@FOO, @BAR(0.2-z+b), @ZOG

Some documentation.
''',
    )
    entry = docorator.parser(entry, adict())
    self.assertEqual(
      sorted(entry.classes),
      sorted(['doc-foo', 'doc-bar', 'doc-bar-0-2-z-b', 'doc-zog']))

  #----------------------------------------------------------------------------
  def test_rst(self):
    from ..test.syntax_docorator import Root
    root = Root()
    root.desc = DescribeController(
      root, doc='URL tree description.',
      settings={
        'formats'        : 'rst',
        'index-redirect' : 'false',
        'exclude'        : ('|^/desc(/.*)?$|'),
        'format.request' : 'true',
      })
    # TODO: remove this `warnings` fiddling when the
    #       numpydoc-not-allowing-custom-section-titles issue
    #       has been resolved.
    import warnings
    with warnings.catch_warnings(record=True) as warns:
      self.assertResponse(
        self.send(root, '/desc?showLegend=false&rstMax=true&showMeta=false'), 200,
        self.loadTestData('syntax_docorator.output.rst'))

  #----------------------------------------------------------------------------
  def test_html(self):
    from ..test.syntax_docorator import Root
    root = Root()
    root.desc = DescribeController(
      root, doc='URL tree description.',
      settings={
        'formats'        : 'html',
        'index-redirect' : 'false',
        'exclude'        : ('|^/desc(/.*)?$|'),
        'format.request' : 'true',
      })
    # TODO: remove this `warnings` fiddling when the
    #       numpydoc-not-allowing-custom-section-titles issue
    #       has been resolved.
    import warnings
    with warnings.catch_warnings(record=True) as warns:
      self.assertResponse(
        self.send(root, '/desc?showLegend=false'), 200,
        self.loadTestData('syntax_docorator.output.html', {
          'version' : getVersion('pyramid_describe'),
        }))

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
