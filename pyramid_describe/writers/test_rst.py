# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2013/10/02
# copy: (C) Copyright 2013 Cadit Health Inc., All Rights Reserved.
#------------------------------------------------------------------------------

import sys, unittest, six

from . import rst

#------------------------------------------------------------------------------
class TestRst(unittest.TestCase):

  maxDiff = None

  #----------------------------------------------------------------------------
  def rt(self, data, writer=None, settings=None):
    from docutils.core import publish_doctree, publish_from_doctree
    dt = publish_doctree(data, settings_overrides=settings)
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
  def test_link_embedded_with_caps(self):
    src = 'a `Link With Space <http://example.com>`_.'
    chk = 'a `Link With Space <http://example.com>`_.\n'
    self.assertMultiLineEqual(self.rt(src), chk)

  #----------------------------------------------------------------------------
  def test_link_implicit(self):
    src = '''\
A link to the `Level 1`_ section.

Level 1
=======

some text.
'''
    chk = '''\
A link to the `Level 1`_ section.

=======
Level 1
=======

some text.
'''
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
    docsect = nodes.section('')
    docsect['classes'] = ('c1 c2',)
    docsect['ids'] = ('my-test-id',)
    docsect.append(nodes.title('', '', nodes.Text('Title')))
    docsect.append(nodes.paragraph('', '', nodes.Text('some text.')))
    docsect.append(
      nodes.section(
        '',
        nodes.title('', '', nodes.Text('Sub-Title')),
        nodes.paragraph('', '', nodes.Text('some more text'))))
    doc.append(nodes.target(refid='my-test-id'))
    doc.append(docsect)
    chk = '''\
.. _`my-test-id`:

.. class:: c1 c2

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
    self.assertMultiLineEqual(self.rt(out, settings={'doctitle_xform': False}), chk)

  #----------------------------------------------------------------------------
  def test_ids_generated(self):
    from docutils import utils, nodes
    from docutils.core import publish_from_doctree
    doc = utils.new_document('<program>')
    docsect = nodes.section('')
    docsect['classes'] = ('c1 c2',)
    docsect['ids'] = ('my-test-id',)
    docsect['target-ids'] = ('my-test-id',)
    docsect.append(nodes.title('', '', nodes.Text('Title')))
    docsect.append(nodes.paragraph('', '', nodes.Text('some text.')))
    docsect.append(
      nodes.section(
        '',
        nodes.title('', '', nodes.Text('Sub-Title')),
        nodes.paragraph('', '', nodes.Text('some more text'))))
    doc.append(docsect)
    chk = '''\
.. class:: c1 c2

.. _`my-test-id`:

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
    doc.append(MetaBody('').meta('', name='one-digit', content='3'))
    chk = '''\
======
Title
======

some text.

.. meta::
    :title: Title
    :generator: pyramid_describe/0.0.0
    :location: http://example.com/
    :one-digit: 3
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

  #----------------------------------------------------------------------------
  def test_problematic(self):
    src = 'this paragraph is not **clean.\n'
    chk = '''\
this paragraph is not `** <#id1>`__\\ clean.

.. class:: system-message

============================
WARNING/2 (<string>, line 1)
============================

Inline strong start-string without end-string.
'''
    out = six.StringIO()
    self.assertMultiLineEqual(self.rt(src, settings={'warning_stream': out}), chk)
    self.assertMultiLineEqual(out.getvalue(), '''\
<string>:1: (WARNING/2) Inline strong start-string without end-string.
''')

  #----------------------------------------------------------------------------
  def test_paragraph_with_class(self):
    src = '.. class:: test beta\n\na paragraph.'
    chk = '.. class:: beta test\n\na paragraph.\n'
    self.assertMultiLineEqual(self.rt(src), chk)

  #----------------------------------------------------------------------------
  def test_table(self):
    src = '''\
some text.

====================  =============================================
Cell 1                Column 2
====================  =============================================
``item 1.1``          item 1.2: **foo**
item 2.1              ``item 2.2``
====================  =============================================

some more text.
'''
    chk = '''\
some text.

==================== =============================================
Cell 1               Column 2
==================== =============================================
``item 1.1``         item 1.2: **foo**
item 2.1             ``item 2.2``
==================== =============================================

some more text.
'''
    self.assertMultiLineEqual(self.rt(src), chk)

## TODO: add support for grid tables...
#   #----------------------------------------------------------------------------
#   def test_table_grid(self):
#     src = '''\
# +------------+------------+-----------+
# | Header 1   | Header 2   | Header 3  |
# +============+============+===========+
# | body row 1 | column 2   | column 3  |
# +------------+------------+-----------+
# | body row 2 | Cells may span columns.|
# +------------+------------+-----------+
# | body row 3 | Cells may  | - Cells   |
# +------------+ span rows. | - contain |
# | body row 4 |            | - blocks. |
# +------------+------------+-----------+
# '''
#     chk = '''\
# +------------+------------+-----------+
# | Header 1   | Header 2   | Header 3  |
# +============+============+===========+
# | body row 1 | column 2   | column 3  |
# +------------+------------+-----------+
# | body row 2 | Cells may span columns.|
# +------------+------------+-----------+
# | body row 3 | Cells may  | - Cells   |
# +------------+ span rows. | - contain |
# | body row 4 |            | - blocks. |
# +------------+------------+-----------+
# '''
#     self.assertMultiLineEqual(self.rt(src), chk)

## TODO: add support for multi-row colspecs...
#   #----------------------------------------------------------------------------
#   def test_table_grid(self):
#     src = '''\
# =====  =====  ======
#    Inputs     Output
# ------------  ------
#   A      B    A or B
# =====  =====  ======
# False  False  False
# True   False  True
# False  True   True
# True   True   True
# =====  =====  ======
# '''
#     chk = '''\
# ===== ===== ======
# Inputs      Output
# ----------- ------
# A     B     A or B
# ===== ===== ======
# False False False
# True  False True
# False True  True
# True  True  True
# ===== ===== ======
# '''
#     self.assertMultiLineEqual(self.rt(src), chk)

  #----------------------------------------------------------------------------
  def test_comment(self):
    src = 'some text.\n\n.. a comment: non-descript, eh?\n\nsome more text.'
    chk = 'some text.\n\n.. a comment: non-descript, eh?\n\nsome more text.\n'
    self.assertMultiLineEqual(self.rt(src), chk)

  #----------------------------------------------------------------------------
  def test_nonlist_text(self):
    src = r'''
\(a) foo

\(1) foo

\(MCMLXX) foo

a\) foo

1\. foo

MCMLXX\) foo
'''
    chk = r'''\(a) foo

\(1) foo

\(MCMLXX) foo

\a) foo

\1. foo

\MCMLXX) foo
'''
    self.assertMultiLineEqual(self.rt(src), chk)

  #----------------------------------------------------------------------------
  def test_email(self):
    src = 'send your comments to asdf@example.com.\n'
    self.assertMultiLineEqual(self.rt(src), src)

  #----------------------------------------------------------------------------
  def test_toplevel_promoted(self):
    src = '''\
Level 1
=======

Level 2
-------

Level 3
~~~~~~~

text 1.2.3
'''
    chk = '''\
=======
Level 1
=======

-------
Level 2
-------

```````
Level 3
```````

text 1.2.3
'''
    self.assertMultiLineEqual(self.rt(src), chk)

  #----------------------------------------------------------------------------
  def test_toplevel_notpromoted(self):
    src = '''\
Level 1
=======

Level 2
-------

Level 1
=======

Level 2
-------
'''
    chk = '''\
=======
Level 1
=======

-------
Level 2
-------

=======
Level 1
=======

-------
Level 2
-------
'''
    self.assertMultiLineEqual(self.rt(src), chk)

  #----------------------------------------------------------------------------
  def test_substitution(self):
    src = '''\
It is 5mm thick |---| |plusmn|\ 0.5mm).

.. |plusmn| unicode:: U+000B1

.. |---| unicode:: U+02014 .. &mdash;
'''
    chk = '''\
It is 5mm thick |---| |plusmn|\ 0.5mm).

.. |plusmn| unicode:: u+000b1

.. |---| unicode:: u+02014
'''
    self.assertMultiLineEqual(self.rt(src), chk)

  #----------------------------------------------------------------------------
  def test_substitution_trims(self):
    src = '.. |blue| replace:: moon\n  :trim:\n'
    chk = '.. |blue| replace:: moon\n    :trim:\n'
    self.assertMultiLineEqual(self.rt(src), chk)
    src = '.. |blue| replace:: moon\n  :ltrim:\n'
    chk = '.. |blue| replace:: moon\n    :ltrim:\n'
    self.assertMultiLineEqual(self.rt(src), chk)
    src = '.. |blue| replace:: moon\n  :rtrim:\n'
    chk = '.. |blue| replace:: moon\n    :rtrim:\n'
    self.assertMultiLineEqual(self.rt(src), chk)
    src = '''\
The AcmeCo |trade|.

.. |trade|  unicode:: U+02122 .. TRADE MARK SIGN
  :ltrim:
'''
    chk = '''\
The AcmeCo\ |trade|.

.. |trade| unicode:: u+02122
    :ltrim:
'''
    self.assertMultiLineEqual(self.rt(src), chk)

  #----------------------------------------------------------------------------
  def test_idcompression(self):
    src = '''\
Level 1
-------

Some Name
~~~~~~~~~

section 1.1.

Level 2
-------

Some Name
~~~~~~~~~

section 1.2.
'''
    chk = '''\
=======
Level 1
=======

---------
Some Name
---------

section 1.1.

=======
Level 2
=======

---------
Some Name
---------

section 1.2.
'''
    self.assertMultiLineEqual(self.rt(src), chk)

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
