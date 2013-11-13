# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2013/10/02
# copy: (C) Copyright 2013 Cadit Health Inc., All Rights Reserved.
#------------------------------------------------------------------------------

import re, textwrap
from docutils import core, utils, nodes, writers
import docutils.writers
from docutils.utils.urischemes import schemes

#------------------------------------------------------------------------------
# TODO: these regex's... their necessity needs to be re-evaluated...

enumlistfmt_re = re.compile(
  r'^\(?([0-9]+|[a-z]|[ivxlcdm]+)[.)]\s', flags=re.IGNORECASE)

plaintexturi_re = re.compile(
  r'^('
  + '|'.join([re.escape(s) for s in schemes.keys()])
  + '):'
  + r'([A-Za-z0-9_.~!*\'();:@&=+$,/?#[\]-]*)'
  + '$')

#------------------------------------------------------------------------------
# TODO: all calls to `rstEscape` need to be revisited...
def rstEscape(text, context=None):
  if context in ('`',):
    if re.match('^[a-zA-Z0-9]+$', text):
      return text
    text = text.replace('\\', '\\\\').replace(context, '\\' + context)
    return context + text + context
  if context in (':',):
    if context not in text and '\\' not in text:
      return text
    return text.replace('\\', '\\\\').replace(context, '\\' + context)

  # todo: it is a bit unclear what *should* be done here... but what
  #       is happening now, is to backslash-escape any text that could
  #       be interpreted as a title under/overline... which is primarily
  #       being used by the `visit_bullet_list` method, to avoid creating:
  #         ``* /``
  #       which generates the warning:
  #         Unexpected possible title overline or transition.
  #         Treating it as ordinary text because it's so short.

  if context != 'para' and len(text) > 0 \
      and text == text[0] * len(text) \
      and not re.match('a-zA-Z0-9', text[0]):
    text = ( '\\' + text[0] ) * len(text)
  else:
    if enumlistfmt_re.match(text):
      text = '\\' + text
  return text

#------------------------------------------------------------------------------
def rstTicks(text):
  return rstEscape(text, context='`')

#------------------------------------------------------------------------------
DEFAULT_SECTION_CHARS = '''=-`:'"~^_*+#<>'''
DEFAULT_TEXT_WIDTH    = 79
DEFAULT_INDENT        = ' '*4

#------------------------------------------------------------------------------
class Writer(writers.Writer):

  supported = ('reStructuredText', 'text', 'txt', 'rst')
  'Formats this writer supports.'

  settings_spec = (
    '"Docutils Canonical reStructuredText" Writer Options',
    None,
    (('Specify the order of over/underline characters.',
      ['--section-chars'],
      {'dest': 'section_chars', 'action': 'store',
       'default': DEFAULT_SECTION_CHARS}),
     ('Set the default indentation text.',
      ['--indent'],
      {'dest': 'indent', 'action': 'store',
       'default': DEFAULT_INDENT}),
     ('Set the text wrapping width.',
      ['--text-width'],
      {'dest': 'text_width', 'action': 'store', 'type': 'int',
       'default': DEFAULT_TEXT_WIDTH}),
     ('Output an explicit `title` directive (even if inferrable).',
      ['--explicit-title'],
      {'dest': 'explicit_title', 'action': 'store_true',
       'default': False}),
     ),)

  config_section = 'rst writer'
  config_section_dependencies = ('writers',)

  output = None
  'Final translated form of `document`.'

  def __init__(self):
    writers.Writer.__init__(self)
    self.translator_class = RstTranslator

  def translate(self):
    self.visitor = visitor = self.translator_class(self.document)
    self.document.walkabout(visitor)
    # todo: translate EOL's here?...
    self.output = visitor.output.data()

#------------------------------------------------------------------------------
def collapseLines(value, step):
  if not step:
    return value
  if step != '\n':
    return value + [step]
  if not value:
    return value
  if len(value) > 2 and value[-1] == '\n' and value[-2] == '\n':
    return value
  return value + [step]

#------------------------------------------------------------------------------
newline_re = re.compile('\n([^\n])')
class Output:
  def __init__(self):
    self.lines = []
  def emptyline(self):
    # todo: improve this
    self.lines.append('\n')
    self.lines.append('\n')
  def newline(self):
    # todo: improve this
    if len(self.lines) > 0 and self.lines[-1] != '\n':
      self.lines.append('\n')
  def append(self, data):
    self.lines.append(data)
  def extend(self, data):
    self.lines.extend(data)
  def data(self, indent=None, first_indent=None, notrail=False):
    ret = ''.join(reduce(collapseLines, self.lines, []))
    if notrail and ret.endswith('\n'):
      ret = ret[:-1]
    if indent is None:
      return ret
    ret = newline_re.sub('\n' + indent.replace('\\', '\\\\') + '\\1', ret)
    if first_indent is False:
      return ret
    if first_indent is None:
      first_indent = indent
    return first_indent + ret

#------------------------------------------------------------------------------
class RstTranslator(nodes.GenericNodeVisitor):

  inline_format = {
    'inline'                          : ('{}',       None),
    'emphasis'                        : ('*{}*',     None),
    'strong'                          : ('**{}**',   None),
    'interpreted_or_phrase_ref'       : ('`{}`',     None),
    'title_reference'                 : ('`{}`',     None),
    'literal'                         : ('``{}``',   None),
    'inline_internal_target'          : ('_{}',      rstTicks),
    'footnote_reference'              : ('[{}]_',    None),
    'substitution_reference'          : ('|{}|',     None),
    'reference'                       : ('{}_',      rstTicks),
    'anonymous_reference'             : ('{}__',     rstTicks),
    }

  #----------------------------------------------------------------------------
  def __init__(self, document):
    nodes.NodeVisitor.__init__(self, document)
    self.settings = document.settings
    self.output   = Output()
    self.stack    = []
    self.tlevel   = 0
    self.cache    = None
    self.cstack   = []

  #----------------------------------------------------------------------------
  def _pushStack(self):
    self.stack.append(self.output)
    self.output = Output()

  #----------------------------------------------------------------------------
  def _popStack(self):
    ret = self.output
    self.output = self.stack.pop()
    return ret

  #----------------------------------------------------------------------------
  def _putAttributes(self, node):
    title = None
    wtitle = False
    if isinstance(node, nodes.document):
      title = self.settings.title
      if title is not None:
        wtitle = True
    if not title:
      title = node.get('title')
    if title is not None:
      wtitle = self.settings.explicit_title or wtitle
      if not wtitle and isinstance(node, nodes.document):
        # check to see if the `document` title is different than
        # the inferred title, in which case we force-show the title
        # todo: is this really the best way to determine the inferred title?
        # todo: is checking for the first `title` node sufficient?
        # todo: there must be a way to use the rst parser code, no?...
        for subnode in node:
          if isinstance(subnode, nodes.title):
            if node.get('title') != subnode.astext():
              wtitle = True
            break
      if wtitle:
        self.output.emptyline()
        self.output.append('.. title:: ' + node['title'])
        self.output.emptyline()
    if node['classes']:
      self.output.emptyline()
      self.output.append('.. class:: ' + ' '.join(sorted(node['classes'])))
      self.output.emptyline()
    if node['ids']:
      # note: only generating an `id` node IFF they are not generated
      # todo: this is *not* the best way to determine whether or not
      #       the node['ids'] is completely generated!...
      dids = self.document.ids
      nids = node['ids']
      node['ids'] = []
      for id in nids:
        # todo: there is a weirdness that if the id references the document,
        #       then self.document.ids lookup points to a `section` node...
        #       look into what i misunderstood here.
        rnode = self.document.ids.get(id)
        if isinstance(node, nodes.document) and isinstance(rnode, nodes.section):
          rnode = node
        if rnode is node:
          del self.document.ids[id]
      self.document.set_id(node)
      nids_ng = set(nids) - set(node['ids'])
      if nids_ng:
        self.output.emptyline()
        for nid in sorted(nids_ng):
          self.output.append('.. _{id}:'.format(id=rstTicks(nid)))
          self.output.emptyline()
      self.document.ids = dids
      node['ids'] = nids

  #----------------------------------------------------------------------------
  def default_visit(self, node):
    if isinstance(node, nodes.Inline):
      self._pushStack()
    else:
      self._putAttributes(node)

  #----------------------------------------------------------------------------
  def default_departure(self, node):
    if isinstance(node, nodes.Inline):
      text = self._popStack().data()
      fmt = self.inline_format[node.__class__.__name__]
      if fmt[1]:
        text = fmt[1](text)
      self.output.append(fmt[0].format(text))

  #----------------------------------------------------------------------------
  def visit_problematic(self, node):
    self._pushStack()

  #----------------------------------------------------------------------------
  def depart_problematic(self, node):
    self._popStack()
    text = rstTicks(node.astext())
    if text.startswith('`'):
      text = text[1:-1]
    # note: wrapping the link with newlines to protect
    # from other surrounding words.
    self.output.newline()
    self.output.append('`{text} <#{refuri}>`__'.format(
      text   = text,
      refuri = node['refid'],
      ))
    self.output.newline()

  #----------------------------------------------------------------------------
  def visit_system_message(self, node):
    kls = node['classes']
    node['classes'] = kls + ['system-message']
    self._putAttributes(node)
    node['classes'] = kls
    self.visit_title(None)
    self.output.append(
      '{type}/{level} ({source}, line {line})'.format(**node.attributes))
    self.depart_title(None)

  #----------------------------------------------------------------------------
  def depart_system_message(self, node):
    pass

  #----------------------------------------------------------------------------
  def visit_document(self, node):
    for subnode in node:
      if isinstance(subnode, nodes.title):
        self.tlevel = 1
      if isinstance(subnode, nodes.subtitle):
        self.tlevel = 2
    return self.default_visit(node)

  #----------------------------------------------------------------------------
  def depart_document(self, node):
    self.output.newline()

  #----------------------------------------------------------------------------
  def visit_Text(self, node):
    self.output.append(rstEscape(node.astext(), 'para'))

  #----------------------------------------------------------------------------
  def visit_title(self, node):
    self._pushStack()

  #----------------------------------------------------------------------------
  def depart_title(self, node):
    sclen = len(self.settings.section_chars)
    level = self.tlevel - 1
    # special handling if lone section titles were promoted to doc-level
    if node and isinstance(node.parent, nodes.document):
      if isinstance(node, nodes.title):
        level = 0
      else:
        level = 1
    if level < 0:
      level = 0
    over  = level < sclen
    lsym  = self.settings.section_chars[level % sclen]
    text  = self._popStack().data(notrail=True)
    if len(text) > 0 and text == text[0] * len(text) and re.match('[^a-zA-Z0-9]', text[0]):
      text = re.sub('([^a-zA-Z0-9])', '\\\\\\1', text)
    width = max(6, len(text))
    self.output.emptyline()
    if over:
      self.output.append(lsym * width)
      self.output.newline()
    self.output.append(text)
    self.output.newline()
    self.output.append(lsym * width)
    self.output.newline()

  #----------------------------------------------------------------------------
  visit_subtitle = visit_title
  depart_subtitle = depart_title

  #----------------------------------------------------------------------------
  def visit_section(self, node):
    self._putAttributes(node)
    self.tlevel += 1

  #----------------------------------------------------------------------------
  def depart_section(self, node):
    self.tlevel -= 1

  #----------------------------------------------------------------------------
  def visit_paragraph(self, node):
    self._putAttributes(node)
    self._pushStack()

  #----------------------------------------------------------------------------
  def depart_paragraph(self, node):
    text = self._popStack().data(notrail=True)
    self.output.emptyline()
    # todo: do textwrapping rules change in rST?...
    self.output.append(
      '\n'.join(textwrap.wrap(text, width=self.settings.text_width)))
    self.output.newline()

  #----------------------------------------------------------------------------
  def visit_literal_block(self, node):
    self._pushStack()

  #----------------------------------------------------------------------------
  def depart_literal_block(self, node):
    text = self._popStack().data(notrail=True)
    self.output.emptyline()
    cmd = '::'
    if 'code' in node['classes']:
      cmd = '.. code-block::'
      if len(node['classes']) > 1:
        classes = node['classes'][:]
        classes.remove('code')
        cmd += ' ' + ' '.join(sorted(classes))
    self.output.append(cmd)
    self.output.emptyline()
    self.output.append(
      self.settings.indent + text.replace('\n', '\n' + self.settings.indent))
    self.output.newline()

  #----------------------------------------------------------------------------
  def visit_target(self, node):
    if isinstance(node.parent, nodes.TextElement) and node.referenced <= 1:
      # note: this is a little weird, but `target`s exist both when a link
      # is inlined AND when generated as
      return
    self.output.emptyline()
    self.output.append('.. _{name}: {uri}'.format(
      name = rstEscape(node['names'][0], context='`'),
      uri  = rstEscape(node['refuri'])))
    self.output.newline()

  #----------------------------------------------------------------------------
  def depart_target(self, node):
    pass

  #----------------------------------------------------------------------------
  def depart_reference(self, node):
    # todo: this is a bit of a hack... if this is an inline reference,
    #       i'm artificially inserting the "TEXT <URI>" output, and
    #       expecting the default handler to wrap it in "`...`_" --
    #       instead, there should be a helper method.
    sibs = list(node.parent)
    idx  = sibs.index(node)
    # todo: the ".lower()" is a little disconcerting here... is there
    #       a better way?...
    if idx + 1 < len(sibs) \
        and isinstance(sibs[idx + 1], nodes.target) \
        and node['name'].lower() in sibs[idx + 1]['names'] \
        and sibs[idx + 1].referenced == 1:
      text = self._popStack().data(notrail=True)
      self._pushStack()
      self.output.append('{text} <{uri}>'.format(
        text = text,
        uri  = rstEscape(node['refuri'])))
    else:
      if plaintexturi_re.match(node['refuri']):
        text = self._popStack().data()
        if node['refuri'] in (text, 'mailto:' + text):
          self.output.append(text)
          return
        # doh! something else! revert!...
        # todo: there *must* be a better explanation.
        self._pushStack()
        self.output.append(text)
    return self.default_departure(node)

  #----------------------------------------------------------------------------
  def visit_meta(self, node):
    sibs = list(node.parent)
    idx  = sibs.index(node)
    if idx == 0 or type(sibs[idx - 1]) is not type(node):
      self.output.emptyline()
      self.output.append('.. meta::')
      self.output.newline()
    self.output.append('{indent}:{name}: {content}'.format(
      indent  = self.settings.indent,
      name    = rstEscape(node['name'], context=':'),
      content = rstEscape(node['content']),
      ))
    self.output.newline()

  #----------------------------------------------------------------------------
  def depart_meta(self, node):
    pass

  #----------------------------------------------------------------------------
  def visit_bullet_list(self, node): pass
  def depart_bullet_list(self, node): pass

  #----------------------------------------------------------------------------
  def visit_list_item(self, node):
    self._pushStack()

  #----------------------------------------------------------------------------
  def depart_list_item(self, node):
    blt  = node.parent.get('bullet', '*')
    text = self._popStack().data(
      indent=' ' * ( len(blt) + 1 ), first_indent=False, notrail=True)
    self.output.emptyline()
    self.output.append(blt + ' ' + rstEscape(text))
    self.output.newline()

  #----------------------------------------------------------------------------
  def visit_definition_list(self, node): pass
  def depart_definition_list(self, node): pass
  def visit_definition_list_item(self, node): pass
  def depart_definition_list_item(self, node): pass

  #----------------------------------------------------------------------------
  def visit_term(self, node):
    self.output.emptyline()

  #----------------------------------------------------------------------------
  def depart_term(self, node):
    self.output.newline()

  #----------------------------------------------------------------------------
  def visit_definition(self, node):
    self._pushStack()

  #----------------------------------------------------------------------------
  def depart_definition(self, node):
    text = self._popStack().data(indent=self.settings.indent, notrail=True)
    self.output.emptyline()
    self.output.append(text)
    self.output.newline()

  #----------------------------------------------------------------------------
  def visit_comment(self, node):
    self._pushStack()

  #----------------------------------------------------------------------------
  def depart_comment(self, node):
    text = self._popStack().data(
      indent=self.settings.indent, first_indent=False, notrail=True)
    self.output.emptyline()
    self.output.append('.. ' + rstEscape(text))
    self.output.newline()

  #----------------------------------------------------------------------------
  def _pushCache(self, cache):
    self.cstack.append(self.cache)
    self.cache = cache

  #----------------------------------------------------------------------------
  def _popCache(self):
    ret = self.cache
    self.cache = self.cstack.pop()
    return ret

  #----------------------------------------------------------------------------
  # TODO: this table rendering needs to be considerable improved!...
  #----------------------------------------------------------------------------

  #----------------------------------------------------------------------------
  def _getTableColspecs(self, node):
    while not isinstance(node, nodes.tgroup):
      node = node.parent
    return [n for n in node if isinstance(n, nodes.colspec)]

  #----------------------------------------------------------------------------
  def visit_table(self, node):
    self.output.emptyline()

  #----------------------------------------------------------------------------
  def depart_table(self, node):
    self.output.newline()

  #----------------------------------------------------------------------------
  def visit_thead(self, node):
    cspecs = self._getTableColspecs(node)
    self.output.newline()
    self.output.append(' '.join(['=' * c['colwidth'] for c in cspecs]))
    self.output.newline()

  #----------------------------------------------------------------------------
  def depart_thead(self, node):
    pass

  #----------------------------------------------------------------------------
  def visit_tbody(self, node):
    return self.visit_thead(node)

  #----------------------------------------------------------------------------
  def depart_tbody(self, node):
    return self.visit_thead(node)

  #----------------------------------------------------------------------------
  def visit_row(self, node):
    self._pushCache(list())

  #----------------------------------------------------------------------------
  def depart_row(self, node):
    entries = self._popCache()
    self.output.newline()
    cspecs = self._getTableColspecs(node)
    if len(cspecs) != len(entries):
      # TODO: tables can be more complex than this...
      # TODO: sound the alarm in a more docutils-ish way...
      raise ValueError('column count mismatch (colspecs: %r, row: %r)',
                       len(cspecs), len(entries))
    for idx, entry in enumerate(entries):
      spec = cspecs[idx]
      entry = entry.strip()
      if '\n' in entry:
        # TODO: tables can be more complex than this...
        # TODO: sound the alarm in a more docutils-ish way...
        raise ValueError('table cell entry contains a newline')
      if len(entry) > spec['colwidth']:
        # TODO: tables can be more complex than this...
        # TODO: sound the alarm in a more docutils-ish way...
        raise ValueError('table cell entry contents exceeds colwidth')
      self.output.append(entry)
      if idx + 1 < len(entries):
        self.output.append(' ' * ( spec['colwidth'] - len(entry) ))
        self.output.append(' ')
    self.output.newline()

  #----------------------------------------------------------------------------
  def visit_entry(self, node):
    self._pushStack()

  #----------------------------------------------------------------------------
  def depart_entry(self, node):
    text = self._popStack().data()
    self.cache.append(text)

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
