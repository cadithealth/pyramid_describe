# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2013/10/02
# copy: (C) Copyright 2013 Cadit Health Inc., All Rights Reserved.
#------------------------------------------------------------------------------

import re
import textwrap
import curses.ascii
from docutils import core, utils, nodes, writers
import docutils.writers
from docutils.utils.urischemes import schemes

#------------------------------------------------------------------------------
# TODO: these regex's... their necessity needs to be re-evaluated...

enumlistfmt_cre = re.compile(
  r'^\(?([0-9]+|[a-z]|[ivxlcdm]+)[.)]\s', flags=re.IGNORECASE)

plaintexturi_cre = re.compile(
  r'^('
  + '|'.join([re.escape(s) for s in schemes.keys()])
  + '):'
  + r'([A-Za-z0-9_.~!*\'();:@&=+$,/?#[\]-]*)'
  + '$'
)

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

  # todo: is this where the check for the need for backslash-escaped
  #       whitespace should be (to protect marked-up nodes that aren't
  #       surrounded by whitespace or punctuation)?...

  if context != 'para' and len(text) > 0 \
      and text == text[0] * len(text) \
      and not re.match('a-zA-Z0-9', text[0]):
    text = ( '\\' + text[0] ) * len(text)
  else:
    if enumlistfmt_cre.match(text):
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

TOKEN_NL   = '{\n}'
TOKEN_LINE = '{\n\n}'
TOKEN_SEP  = '{ }'
TOKENS     = (TOKEN_NL, TOKEN_LINE, TOKEN_SEP)

PUNCT_START = '''-:/'"<([{'''
PUNCT_END   = '''-.,:;!?\/'")]}>'''
PUNCT_BOTH  = ''.join(set(PUNCT_START + PUNCT_END))

#------------------------------------------------------------------------------
def collapseTokens(value, step):
  if not step:
    return value
  if not value:
    return [step]
  prev = value.pop()
  ptok = prev in TOKENS
  stok = step in TOKENS
  # if both are text
  if not ( ptok or stok ):
    return value + [prev + step]
  # if either one is text
  if not ( ptok and stok ):
    return value + [prev, step]
  # both are tokens -- collapse
  if prev == step:
    return value + [prev]
  if TOKEN_LINE in (prev, step):
    return value + [TOKEN_LINE]
  # one is a NL and one a SEP
  return value [TOKEN_NL]

#------------------------------------------------------------------------------
newline_re = re.compile('\n([^\n])')
class Output:
  def __init__(self):
    self.tokens = []
  def emptyline(self):
    self.tokens.append(TOKEN_LINE)
    # # todo: improve this
    # self.tokens.append('\n')
    # self.tokens.append('\n')
  def newline(self):
    self.tokens.append(TOKEN_NL)
    # # todo: improve this
    # if len(self.tokens) > 0 and self.tokens[-1] != '\n':
    #   self.tokens.append('\n')
  def separator(self):
    self.tokens.append(TOKEN_SEP)
  def append(self, data):
    self.tokens.append(data)
  def extend(self, data):
    self.tokens.extend(data)
  def data(self, indent=None, first_indent=None, notrail=False):
    tmp = reduce(collapseTokens, self.tokens, [])
    ret = []
    for idx, cur in enumerate(tmp):
      if cur not in TOKENS:
        ret.append(cur)
        continue
      bef = tmp[idx - 1] if idx > 0 else None
      aft = tmp[idx + 1] if idx + 1 < len(tmp) else None
      if cur in (TOKEN_NL, TOKEN_LINE):
        if bef is None:
          continue
        count = 0
        if bef and bef[-1] == '\n':
          count += 1
          if len(bef) > 1 and bef[-2] == '\n':
            count += 1
        if aft and aft[0] == '\n':
          count += 1
          if len(aft) > 1 and aft[1] == '\n':
            count += 1
        if cur == TOKEN_NL:
          count -= 1
        else:
          count -= 2
        if count >= 0:
          continue
        ret.append('\n' * ( 0 - count ))
        continue
      if cur == TOKEN_SEP:
        if not bef or not aft:
          continue
        bef = bef[-1]
        aft = aft[0]
        try:
          if bef == str(bef):
            bef = str(bef)
        except: pass
        try:
          if aft == str(aft):
            aft = str(aft)
        except: pass
        # todo: perhaps the separator direction also needs to be specified...
        #       (i.e. before or after)
        if curses.ascii.isspace(bef) or curses.ascii.isspace(aft) \
            or bef in PUNCT_BOTH or aft in PUNCT_BOTH:
          continue
        ret.append('\\ ')
        continue
      raise ValueError('unexpected output token "%r"' % (cur,))
    ret = ''.join(ret)
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
    self.ostack   = []
    self.tlevel   = 0
    self.cache    = None
    self.cstack   = []
    self.subs     = {node.astext(): node
                     for node in document.substitution_defs.values()}

  #----------------------------------------------------------------------------
  def _pushOutput(self):
    # todo: the problem with many of the pushOutputs is that they
    #       don't explicitly increase the indent level (although they
    #       will be on poOutput)...
    self.ostack.append(self.output)
    self.output = Output()

  #----------------------------------------------------------------------------
  def _popOutput(self):
    ret = self.output
    self.output = self.ostack.pop()
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
    tids = node.get('target-ids', None)
    if tids:
      self.output.emptyline()
      for nid in sorted(tids):
        self.output.append('.. _{id}:'.format(id=rstTicks(nid)))
        self.output.emptyline()

  #----------------------------------------------------------------------------
  def default_visit(self, node):
    if isinstance(node, nodes.Inline):
      self._pushOutput()
    elif isinstance(node, nodes.Admonition):
      self.default_visit_admonition(node)
    else:
      self._putAttributes(node)

  #----------------------------------------------------------------------------
  def default_departure(self, node, fmt=None):
    if isinstance(node, nodes.Inline):
      text = self._popOutput().data()
      fmt = self.inline_format[fmt or node.__class__.__name__]
      if fmt[1]:
        text = fmt[1](text)
      self.output.append(fmt[0].format(text))
    elif isinstance(node, nodes.Admonition):
      self.default_depart_admonition(node)

  #----------------------------------------------------------------------------
  def visit_problematic(self, node):
    self._pushOutput()

  #----------------------------------------------------------------------------
  def depart_problematic(self, node):
    self._popOutput()
    text = rstTicks(node.astext())
    if text.startswith('`'):
      text = text[1:-1]
    # note: wrapping the link with newlines to protect
    # from other surrounding words.
    self.output.separator()
    self.output.append('`{text} <#{refuri}>`__'.format(
      text   = text,
      refuri = node['refid'],
    ))
    self.output.separator()

  #----------------------------------------------------------------------------
  def visit_system_message(self, node):
    kls = node['classes']
    node['classes'] = kls + ['system-message']
    self._putAttributes(node)
    node['classes'] = kls
    self.tlevel += 1
    self.visit_title(None)
    kw = {'type': '??', 'level': '??', 'source': '??', 'line': '??'}
    kw.update(**node.attributes)
    self.output.append('{type}/{level} ({source}, line {line})'.format(**kw))
    self.depart_title(None)
    self.tlevel -= 1

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
    text = node.astext()
    sub  = self.subs.get(text, None)
    if sub is None:
      return self.output.append(rstEscape(text, 'para'))
    self.output.separator()
    self.output.append('|' + sub['names'][0] + '|')
    self.output.separator()

  #----------------------------------------------------------------------------
  def visit_title(self, node):
    self._pushOutput()

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
    text  = self._popOutput().data(notrail=True)
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
    self._pushOutput()

  #----------------------------------------------------------------------------
  def depart_paragraph(self, node):
    text = self._popOutput().data(notrail=True)
    self.output.emptyline()
    # todo: do textwrapping rules change in rST?...
    self.output.append(
      '\n'.join(textwrap.wrap(
        text,
        width            = self.settings.text_width,
        break_long_words = False,
        break_on_hyphens = False,
      )))
    self.output.newline()

  #----------------------------------------------------------------------------
  def default_visit_admonition(self, node):
    self._pushOutput()

  #----------------------------------------------------------------------------
  def default_depart_admonition(self, node):
    text = self._popOutput().data(indent=self.settings.indent, notrail=True)
    self.output.emptyline()
    self._putAttributes(node)
    self.output.append('.. %s::' % (node.__class__.__name__,))
    if text.strip():
      self.output.emptyline()
      self.output.append(text)
    self.output.newline()

  #----------------------------------------------------------------------------
  def visit_literal_block(self, node):
    self._pushOutput()

  #----------------------------------------------------------------------------
  def depart_literal_block(self, node):
    text = self._popOutput().data(notrail=True)
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
    if node.get('names') and node.get('refuri'):
      self.output.append('.. _{name}: {uri}'.format(
        name = rstEscape(node['names'][0], context='`'),
        uri  = rstEscape(node['refuri'])))
    elif node.get('anonymous') and node.get('refuri'):
      self.output.append('__ {uri}'.format(uri=rstEscape(node['refuri'])))
    elif node.get('refid'):
      self.output.append('.. _{id}:'.format(
        id=rstEscape(node['refid'], context='`')))
    else:
      raise ValueError('target without names+refuri, anon+refuri, or refid')
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
    fmt  = None
    # todo: the ".lower()" is a little disconcerting here... is there
    #       a better way?...
    #       ==> perhaps use `nodes.fully_normalize_name()`
    if idx + 1 < len(sibs) \
        and isinstance(sibs[idx + 1], nodes.target) \
        and node['name'].lower() in sibs[idx + 1]['names'] \
        and sibs[idx + 1].referenced == 1:
      text = self._popOutput().data().strip()
      self._pushOutput()
      self.output.append('{text} <{uri}>'.format(
        text = text,
        uri  = rstEscape(node.get('refuri', node.get('refid', '')))))
    else:
      if 'refuri' in node:
        if plaintexturi_cre.match(node['refuri']):
          text = self._popOutput().data()
          if node['refuri'] in (text, 'mailto:' + text):
            self.output.append(text)
            return
          self._pushOutput()
          self.output.append(text)
          if 'name' in node and nodes.make_id(node['name']) not in self.document.ids:
            if not node.get('anonymous'):
              self.output.append(' <{uri}>'.format(uri=rstEscape(node.get('refuri'))))
            fmt = 'anonymous_reference'
      elif 'refid' in node:
        text = self._popOutput().data().strip()
        if text != node.get('name', ''):
          self.document.reporter.warning(
            'implicit reference text does not match reference name... ignoring ref-name')
        if nodes.fully_normalize_name(text) \
            not in self.document.ids[node['refid']].get('names', []):
          self.document.reporter.error(
            'implicit reference text does not match target name... ignoring')
        self._pushOutput()
        self.output.append(text)
      else:
        self.document.reporter.warning(
          'reference with neither ref-uri nor ref-id... ignoring')
        self._pushOutput()
        self.output.append(text)
    return self.default_departure(node, fmt=fmt)

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
      # todo: revisit rstEscape!... (and def. this 'para' context...)
      content = rstEscape(node['content'], context='para'),
    ))
    self.output.newline()

  #----------------------------------------------------------------------------
  def depart_meta(self, node):
    pass

  #----------------------------------------------------------------------------
  def visit_image(self, node):
    # todo: generalize this...
    if node.parent and node.parent.tagname in ('figure',):
      return
    self._putImage(node)

  #----------------------------------------------------------------------------
  def _putImage(self, node, directive='image', override_attributes=None):
    self.output.emptyline()
    self.output.append('.. {name}:: {uri}'.format(
      name = directive,
      uri  = rstEscape(node.get('uri'), context='para')
    ))
    self.output.newline()
    attributes = dict(node.attributes.items())
    if override_attributes:
      attributes.update(override_attributes)
    for attr in sorted(attributes.keys()):
      if attr in ('uri', 'ids', 'backrefs', 'dupnames', 'classes', 'names'):
        continue
      self.output.append('{indent}:{name}: {content}'.format(
        indent  = self.settings.indent,
        name    = rstEscape(attr, context=':'),
        # todo: revisit rstEscape!... (and def. this 'para' context...)
        content = rstEscape(attributes.get(attr), context='para'),
      ))
      self.output.newline()
    self.output.newline()

  #----------------------------------------------------------------------------
  def depart_image(self, node):
    pass

  #----------------------------------------------------------------------------
  def visit_figure(self, node):
    if not node.children or node.children[0].tagname != 'image':
      raise ValueError('figure without image')
    self._putImage(
      node.children[0], directive='figure', override_attributes=node.attributes)
    self._pushOutput()

  #----------------------------------------------------------------------------
  def depart_figure(self, node):
    text = self._popOutput().data(indent=self.settings.indent, notrail=True)
    if text.strip():
      self.output.emptyline()
      self.output.append(text)
    self.output.newline()

  #----------------------------------------------------------------------------
  def visit_bullet_list(self, node): pass
  def depart_bullet_list(self, node): pass

  #----------------------------------------------------------------------------
  def visit_list_item(self, node):
    self._pushOutput()

  #----------------------------------------------------------------------------
  def depart_list_item(self, node):
    if isinstance(node.parent, nodes.bullet_list):
      blt = node.parent.get('bullet', '*')
    elif isinstance(node.parent, nodes.enumerated_list):
      # todo: be sensitive to `node.parent.get('enumtype')`...
      blt = str(node.parent.children.index(node) + 1)
      blt += node.parent.get('suffix', '.')
    else:
      # TODO: i *should* throw:
      #         raise ValueError('unknown list type: %r' % (node.parent,))
      #       but because of the issue in pyramid_describe/render.py:renderDocEndpoint
      #       i can't... fix!
      blt = node.parent.get('bullet', '*')
    text = self._popOutput().data(
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
    self._pushOutput()

  #----------------------------------------------------------------------------
  def depart_definition(self, node):
    text = self._popOutput().data(indent=self.settings.indent, notrail=True)
    self.output.emptyline()
    self.output.append(text)
    self.output.newline()

  #----------------------------------------------------------------------------
  def visit_comment(self, node):
    self._pushOutput()

  #----------------------------------------------------------------------------
  def depart_comment(self, node):
    text = self._popOutput().data(
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
  # SUBSTITUTIONS
  #----------------------------------------------------------------------------

  #----------------------------------------------------------------------------
  def visit_substitution_definition(self, node):
    self._pushOutput()
    self._pushCache(self.subs)
    self.subs = {}

  #----------------------------------------------------------------------------
  def depart_substitution_definition(self, node):
    text = self._popOutput().data(
      indent=self.settings.indent, first_indent=False, notrail=True)
    self.subs = self._popCache()
    for name in node['names']:
      # TODO: this special-casing is a bit ridiculous...
      if len(text) == 1 and not curses.ascii.isalnum(text):
        text = 'unicode:: u+{:0>5x}'.format(ord(text),)
      else:
        text = 'replace:: ' + rstEscape(text)
      self.output.emptyline()
      self.output.append('.. |' + name + '| ' + text)
      self.output.newline()
      ltrim = bool(node.get('ltrim', False))
      rtrim = bool(node.get('rtrim', False))
      if ltrim or rtrim:
        if ltrim and rtrim:
          trim = ':trim:'
        elif ltrim:
          trim = ':ltrim:'
        else:
          trim = ':rtrim:'
        self.output.append(self.settings.indent + trim)
        self.output.newline()

  # todo: these don't seem to get called...
  # def visit_substitution_reference(self, node): ...
  # def depart_substitution_reference(self, node): ...

  #----------------------------------------------------------------------------
  # TODO: this table rendering needs to be considerably improved!...
  #----------------------------------------------------------------------------

  #----------------------------------------------------------------------------
  def _getTableColspecs(self, node):
    while not isinstance(node, nodes.tgroup):
      node = node.parent
    return [n for n in node if isinstance(n, nodes.colspec)]

  #----------------------------------------------------------------------------
  def visit_table(self, node):
    self.output.emptyline()
    self._putAttributes(node)

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
    self._pushOutput()

  #----------------------------------------------------------------------------
  def depart_entry(self, node):
    text = self._popOutput().data()
    self.cache.append(text)

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
