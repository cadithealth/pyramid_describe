# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2013/10/02
# copy: (C) Copyright 2013 Cadit Health Inc., All Rights Reserved.
#------------------------------------------------------------------------------

import sys, unittest
from . import rst

#------------------------------------------------------------------------------
class TestRst(unittest.TestCase):

  maxDiff = None

  #----------------------------------------------------------------------------
  def rt(self, data, writer=None, settings=None):
    from docutils.core import publish_doctree, publish_from_doctree
    dt = publish_doctree(data)
    return publish_from_doctree(dt,
                                writer=writer or rst.Writer(),
                                settings_overrides=settings)

  #----------------------------------------------------------------------------
  def test_simple(self):
    src = '''\
.. class:: class1 class2

`Local` *Top-Level* ``10``
~~~~~~~~~~~~~~~~~~~~~~~~~~

some `link`_ foo.

Sub-Title
#########

more text

.. _`link`: http://foo.bar.com/
'''
    chk = '''\
.. class:: class1 class2

==========================
`Local` *Top-Level* ``10``
==========================

some link_ foo.

---------
Sub-Title
---------

more text

.. _link: http://foo.bar.com/
'''
    out = self.rt(src)
    self.assertMultiLineEqual(out, chk)

  #----------------------------------------------------------------------------
  def test_explicit_title(self):
    src = 'My *Title*\n----------\n\nsome text.\n'
    chk = '==========\nMy *Title*\n==========\n\nsome text.\n'
    out = self.rt(src)
    self.assertMultiLineEqual(out, chk)
    chk = '.. title:: My Title\n\n' + chk
    out = self.rt(src, settings={'explicit_title': True})
    self.assertMultiLineEqual(out, chk)

  #----------------------------------------------------------------------------
  def test_altered_title(self):
    from docutils import utils, nodes
    from docutils.core import publish_from_doctree
    doc = utils.new_document('<program>')
    doc['title']   = 'Altered Title'
    doc.append(nodes.title('', '', nodes.Text('Title')))
    doc.append(nodes.paragraph('', '', nodes.Text('some text.')))
    chk = '.. title:: Altered Title\n\n======\nTitle\n======\n\nsome text.\n'
    out = publish_from_doctree(
      doc, writer=rst.Writer(), settings_overrides={'explicit_title': False})
    self.assertMultiLineEqual(out, chk)

  #----------------------------------------------------------------------------
  def test_link(self):
    src = '''\
a `link with space`_.

.. _`link with space`: http://example.com/
'''
    self.assertMultiLineEqual(self.rt(src), src)

  #----------------------------------------------------------------------------
  def test_link_embedded(self):
    src = 'a `link with space <http://example.com>`_.'
    chk = 'a `link with space <http://example.com>`_.\n'
    self.assertMultiLineEqual(self.rt(src), chk)

  #----------------------------------------------------------------------------
  def test_literal_block(self):
    src = 'A literal example::\n\n  Code Line 1\n  ==> code line 2\n'
    chk = 'A literal example:\n\n::\n\n    Code Line 1\n    ==> code line 2\n'
    out = self.rt(src)
    self.assertMultiLineEqual(out, chk)

  #----------------------------------------------------------------------------
  def test_code_block(self):
    src = 'A literal example:\n\n.. code-block::\n\n  Code Line 1\n  ==> code line 2\n'
    chk = 'A literal example:\n\n.. code-block::\n\n    Code Line 1\n    ==> code line 2\n'
    out = self.rt(src)
    self.assertMultiLineEqual(out, chk)

  #----------------------------------------------------------------------------
  def test_code_block_python(self):
    try:
      import pygments
    except ImportError:
      sys.stderr.write('*** PYGMENTS LIBRARY NOT PRESENT - SKIPPING *** ')
      return
    src = 'A literal example:\n\n.. code-block:: python\n\n  import sys\n  sys.stdout.write("hello!")\n'
    chk = 'A literal example:\n\n.. code-block:: python\n\n    import sys\n    sys.stdout.write("hello!")\n'
    out = self.rt(src)
    self.assertMultiLineEqual(out, chk)

  #----------------------------------------------------------------------------
  def test_ids(self):
    from docutils import utils, nodes
    from docutils.core import publish_from_doctree
    doc = utils.new_document('<program>')
    doc['classes'] = ('c1 c2',)
    doc['ids'] = ('my-test-id',)
    doc.append(nodes.title('', '', nodes.Text('Title')))
    doc.append(nodes.paragraph('', '', nodes.Text('some text.')))
    doc.append(
      nodes.section(
        '',
        nodes.title('', '', nodes.Text('Sub-Title')),
        nodes.paragraph('', '', nodes.Text('some more text'))))
    chk = '''\
.. class:: c1 c2

.. id:: my-test-id

======
Title
======

some text.

---------
Sub-Title
---------

some more text
'''
    out = publish_from_doctree(doc, writer=rst.Writer())
    self.assertMultiLineEqual(out, chk)

  #----------------------------------------------------------------------------
  def test_meta(self):
    from docutils import utils, nodes
    from docutils.parsers.rst.directives.html import MetaBody
    from docutils.core import publish_from_doctree
    doc = utils.new_document('<program>')
    doc.append(nodes.title('', '', nodes.Text('Title')))
    doc.append(nodes.paragraph('', '', nodes.Text('some text.')))
    doc.append(MetaBody('').meta('', name='title', content='Title'))
    doc.append(MetaBody('').meta('', name='generator', content='pyramid_describe/0.0.0'))
    doc.append(MetaBody('').meta('', name='location', content='http://example.com/'))
    chk = '''\
======
Title
======

some text.

.. meta::
    :title: Title
    :generator: pyramid_describe/0.0.0
    :location: http://example.com/
'''
    out = publish_from_doctree(
      doc, writer=rst.Writer(), settings_overrides={'explicit_title': False})
    self.assertMultiLineEqual(out, chk)

  #----------------------------------------------------------------------------
  def test_lists(self):
    src = '''\
Current list of **states**
that this
engine can be in:

* beta
* production
* deprecated (this is a long line to cause
  the text handler to wrap it to the next line,
  and therefore test the indentation that must be
  done)

The following `skill` levels exist:

``Novice``:
  a true beginner.

``Intermediate``:
  an average user, *usually* expressed with::

    import average_user
    average_user.express()

``Expert``:
  the sky is the limit.
'''
    chk = '''\
Current list of **states** that this engine can be in:

* beta

* production

* deprecated (this is a long line to cause the text handler to wrap it to the
  next line, and therefore test the indentation that must be done)

The following `skill` levels exist:

``Novice``:

    a true beginner.

``Intermediate``:

    an average user, *usually* expressed with:

    ::

        import average_user
        average_user.express()

``Expert``:

    the sky is the limit.
'''
    self.assertMultiLineEqual(self.rt(src), chk)

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
