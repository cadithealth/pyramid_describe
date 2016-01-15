# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2013/10/02
# copy: (C) Copyright 2013 Cadit Health Inc., All Rights Reserved.
#------------------------------------------------------------------------------

'''
This module helps with converting a pyramid-describe data structure to
a docutils "doctree".
'''

import collections
import json
import uuid

import six
import yaml
from docutils import utils, nodes, core
from docutils.core import publish_from_doctree
from docutils.parsers.rst.directives.html import MetaBody
from pyramid_controllers.util import getVersion

from .i18n import _
from .typereg import Type, TypeRef
from . import params

#------------------------------------------------------------------------------
def rtitle(text, *args, **kw):
  return nodes.title('', '', text, *args, **kw)
def rpara(*args, **kw):
  return nodes.paragraph('', '', *args, **kw)
def rtext(text, *args, **kw):
  return nodes.Text(text, *args, **kw)
def rliteral(text, *args, **kw):
  return nodes.literal('', rtext(text, *args, **kw))
def rsect(title, *args, **kw):
  if isinstance(title, six.string_types):
    return nodes.section('', rtitle(rtext(title)), *args, **kw)
  return nodes.section('', rtitle(title), *args, **kw)
def rcont(*args, **kw):
  return nodes.container('', *args, **kw)
Meta = MetaBody('').meta
def rmeta(*args, **kw):
  return Meta('', *args, **kw)
def rref(text, target=None, *args, **kw):
  if target and 'refid' not in kw and 'refuri' not in kw:
    kw['refid'] = target
  return nodes.reference('', rtext(text), *args, **kw)

#------------------------------------------------------------------------------
def rst2document(text, promote=False):
  '''
  The `promote` parameter controls whether or not certain lone section
  titles are promoted to document title (for a lone top-level section)
  and document subtitle (for a lone second-level section).
  '''

  # todo: when there are errors with the input, this generates somewhat
  # confusing error output to STDERR, eg:
  #   <string>:12: (WARNING/2) Inline strong start-string without end-string.
  # it would be *great* if '<string>' were replaced with the actual error
  # source, i.e. controller/method/docstring/etc.

  # TODO: optional failure behaviour: convert the entire
  #       text to a paragraph via:
  #         return [rpara(rtext(text))]
  #       ==> requires error detection.

  # NOTE: this is also used by `.render.render()`

  settings = dict(
    doctitle_xform       = promote,
    sectsubtitle_xform   = promote,
  )
  return core.publish_doctree(text, settings_overrides=settings)

#------------------------------------------------------------------------------
def document2rst(doc):
  '''
  Serializes the docutils Doctree structure `doc` to a
  reStructuredText-formatted text string.
  '''
  if not doc:
    return ''
  from pyramid_describe.writers.rst import Writer
  settings = dict(
    doctitle_xform       = False,
    sectsubtitle_xform   = False,
  )
  return publish_from_doctree(
    doc, writer=Writer(), settings_overrides=settings)

#------------------------------------------------------------------------------
def rst2fragments(text):
  if not text:
    return []
  # TODO: see rst2document for error handling notes...
  return list(rst2document(text))

# TODO: perhaps all these functions would be much simpler if rstMax was
#       checked once, at exit, and if false, all classes and ids were
#       removed?...

#------------------------------------------------------------------------------
def walk(node):
  yield node
  # TODO: should this just be ``for child in node:`` ?
  for child in list(getattr(node, 'children', [])):
    for sub in walk(child):
      yield sub

#------------------------------------------------------------------------------
def render(data):
  doc = utils.new_document('<pyramid_describe.document>')
  # todo:
  # doc.settings.text_width = data.options.width

  title = render_title(data)
  if data.options.rstMax:
    doc['title'] = title

  # todo: test this bullet_list stuff (i.e. set showInfo to false)

  mainsect = rsect(title)
  if data.options.rstMax:
    mainsect['ids'] = ['section-contents']
    mainsect['target-ids'] = mainsect['ids']
    mainsect['classes'] = ['contents']

  endpoints = rsect(data.options.get('endpoints.title') or _('Endpoints'))
  epcont = endpoints
  if data.options.rstMax:
    endpoints['ids'] = ['section-endpoints']
    endpoints['target-ids'] = endpoints['ids']
    endpoints['classes'] = ['endpoints']
  if not data.options.showInfo:
    epcont = nodes.bullet_list('', bullet='*')
    endpoints.append(epcont)
  for endpoint in data.endpoints:
    epcont.append(render_entry(data, endpoint))
  mainsect.append(endpoints)

  mainsect.extend(render_typereg(data))

  if data.options.showLegend:
    legend = rsect(data.options.get('legend.title') or _('Legend'))
    if data.options.rstMax:
      legend['ids'] = ['section-legend']
      legend['target-ids'] = legend['ids']
      legend['classes'] = ['legend']
    for item, desc in data.legend:
      section = rsect(item, rpara(rtext(desc)))
      if data.options.rstMax:
        section['ids'] = ['legend-item-' + data.options.idEncoder(item)]
        section['target-ids'] = section['ids']
        section['classes'] = ['legend-item']
      legend.append(section)
    mainsect.append(legend)

  doc.append(mainsect)
  doc.extend(render_meta(data, title))

  # todo: shouldn't this be done automatically by appending a node
  #       to the document?!?!?.... ugh.
  for node in walk(doc):
    if hasattr(node, 'get'):
      for nid in node.get('ids', []):
        doc.ids[nid] = node
  # /todo

  return doc

#------------------------------------------------------------------------------
def render_title(data):
  return data.options.title or _('Contents of "{}"', data.root)

#------------------------------------------------------------------------------
def render_meta(data, title):
  if not data.options.showMeta:
    return []
  title = title or render_title(data)
  meta = rcont()
  meta.append(rmeta(name='title', content=title))
  if data.options.showGenerator:
    gen = 'pyramid-describe'
    if data.options.showGenVersion:
      gen += '/' + getVersion('pyramid_describe')
    gen += ' [format={}]'.format(data.options.formatstack[-1])
    meta.append(rmeta(name='generator', content=gen))
  if data.options.showLocation and data.options.context.request.url:
    meta.append(rmeta(name='location', content=data.options.context.request.url))
  if data.options.rstMax and data.options.rstPdfkit:
    options = yaml.load(data.options.get('pdfkit.options', '{}'))
    for key in sorted(options.keys()):
      value = options.get(key)
      meta.append(rmeta(name='pdfkit-' + key, content=str(value)))
  return [meta]

#------------------------------------------------------------------------------
def render_entry(data, entry):
  if not data.options.showInfo:
    return nodes.list_item('', rpara(rtext(entry.dpath)))
  section = rsect(entry.dpath)
  section['path']       = entry.path
  section['dpath']      = entry.dpath
  if data.options.rstMax:
    section['ids']        = [entry.id]
    section['target-ids'] = section['ids']
    section['classes']    = ['endpoint'] + ( entry.classes or [] )
  section.extend(render_entry_body(data, entry))
  return section

#------------------------------------------------------------------------------
def render_entry_body(data, entry):
  ret = []
  if data.options.showImpl and entry.ipath:
    impl = _(
      'Handler: {}{} [{}]',
      entry.ipath,'()' if entry.itype == 'instance' else '', entry.itype)
    impl = rpara(rtext(impl))
    if data.options.rstMax:
      impl['ids'] = ['handler-' + entry.id]
      impl['target-ids'] = impl['ids']
      impl['classes'] = ['handler']
    ret.append(impl)

  frags = rst2fragments(entry.doc)
  frags = extend_entry_params(data, entry, frags)
  frags = extend_entry_returns(data, entry, frags)
  frags = extend_entry_raises(data, entry, frags)
  ret.extend(frags)
  ret.extend(render_entry_methods(data, entry))
  return ret

#------------------------------------------------------------------------------
def render_entry_methods(data, entry):
  if not data.options.showRest or not entry.methods:
    return []
  section = rsect(_('Methods'))
  if data.options.rstMax:
    section['ids'] = ['methods-' + entry.id]
    section['target-ids'] = section['ids']
    section['classes'] = ['methods']
  for meth in entry.methods:
    msect = rsect(meth.method or meth.name)
    if data.options.rstMax:
      msect['ids'] = [meth.id]
      msect['target-ids'] = msect['ids']
      msect['classes'] = ['method'] + ( meth.classes or [] )
    msect.extend(render_entry_body(data, meth))
    section.append(msect)
  return [section]

#------------------------------------------------------------------------------
def extend_entry_params(data, entry, fragments):
  section = find_section(fragments, 'Parameters', create=bool(entry.params))
  if not section:
    return fragments
  if data.options.rstMax:
    # todo: check if `ids` has already been set?...
    section['ids'] = ['params-' + entry.id]
    section['target-ids'] = section['ids']
    section['classes'] = ['params'] + list(section.get('classes', []))
  for rnode, rtype in render_polytype(data, entry, 'input', entry.params):
    if data.options.rstMax:
      rnode['ids'] = ['param-' + entry.id + '-' + data.options.idEncoder(rtype)]
      rnode['target-ids'] = rnode['ids']
      rnode['classes'] = ['param'] + list(rnode.get('classes', []))
    section.append(rnode)
  return fragments

#------------------------------------------------------------------------------
def extend_entry_returns(data, entry, fragments):
  section = find_section(fragments, 'Returns', create=bool(entry.returns))
  if not section:
    return fragments
  if data.options.rstMax:
    # todo: check if `ids` has already been set?...
    section['ids'] = ['returns-' + entry.id]
    section['target-ids'] = section['ids']
    section['classes'] = ['returns'] + list(section.get('classes', []))
  for rnode, rtype in render_polytype(data, entry, 'output', entry.returns):
    if data.options.rstMax:
      rnode['ids'] = ['return-' + entry.id + '-' + data.options.idEncoder(rtype)]
      rnode['target-ids'] = rnode['ids']
      rnode['classes'] = ['return'] + list(rnode.get('classes', []))
    section.append(rnode)
  return fragments

#------------------------------------------------------------------------------
def extend_entry_raises(data, entry, fragments):
  section = find_section(fragments, 'Raises', create=bool(entry.raises))
  if not section:
    return fragments
  if data.options.rstMax:
    # todo: check if `ids` has already been set?...
    section['ids'] = ['raises-' + entry.id]
    section['target-ids'] = section['ids']
    section['classes'] = ['raises'] + list(section.get('classes', []))
  for rnode, rtype in render_polytype(data, entry, 'error', entry.raises):
    if data.options.rstMax:
      rnode['ids'] = ['raise-' + entry.id + '-' + data.options.idEncoder(rtype)]
      rnode['target-ids'] = rnode['ids']
      rnode['classes'] = ['raise'] + list(rnode.get('classes', []))
    section.append(rnode)
  return fragments

#------------------------------------------------------------------------------
def find_section(fragments, name, create=True):
  for frag in fragments:
    if isinstance(frag, nodes.section) \
        and frag.children and len(frag.children) >= 1 \
        and isinstance(frag.children[0], nodes.title) \
        and frag.children[0].astext() == name:
      return frag
  if not create:
    return None
  section = rsect(name)
  fragments.append(section)
  return section

#------------------------------------------------------------------------------
def render_type_spec(data, typ):
  if typ.base == Type.CONSTANT:
    # todo: this will *NOT* be round-trip parseable... fix!
    if typ.name in (Type.NULL,):
      return [rtext(json.dumps(typ.value))]
    return [rliteral(json.dumps(typ.value))]
  if typ.base == Type.SCALAR:
    return [rtext(typ.name)]
  if typ.base == Type.COMPOUND:
    ret = [rtext(typ.name)] if typ.name not in (Type.ONEOF, Type.UNION) else []
    sub = []
    if typ.name != Type.DICT:
      for idx, child in enumerate(typ.children):
        if idx > 0:
          if typ.name == Type.ONEOF:
            sub.append(rtext(' ' + data.typereg.options.oneof_sep + ' '))
          elif typ.name == Type.UNION:
            sub.append(rtext(' ' + data.typereg.options.union_sep + ' '))
          else:
            raise ValueError(
              'unexpected/unknown type with multiple children: %r' % (typ,))
        sub.extend(render_type_spec(data, child))
    if not ret and not sub:
      raise ValueError(
        'unexpected/unknown type with no nodes: %r' % (typ,))
    if sub:
      braced = len(sub) > 2 \
        and sub[0].astext().strip() == data.typereg.options.closure_open \
        and sub[-1].astext().strip() == data.typereg.options.closure_close
      if not braced:
        ret.append(rtext(data.typereg.options.closure_open))
      ret.extend(sub)
      if not braced:
        ret.append(rtext(data.typereg.options.closure_close))
    return ret
  if typ not in data.types:
    return [rtext(data.options.get('typereg.noDef') or _('N/A'))]
  if not data.options.rstMax:
    return [rtext(typ.name)]
  target = '#typereg-type-{}'.format(data.options.idEncoder(typ.name))
  # TODO: figure out why this UUID is necessary...
  name   = str(uuid.uuid4())
  return [rref(typ.name, name=name, refuri=target)]

#------------------------------------------------------------------------------
def render_type(data, typ, link=True):

  if isinstance(typ, Type):

    if typ.base == Type.COMPOUND and typ.name == Type.DICT:
      node = rcont()
      node.extend(rst2fragments(typ.doc))
      for sub in typ.value:
        node.append(render_type(data, sub))
      return rsect(Type.DICT, node)

    if typ.base in (Type.DICT, Type.EXTENSION):

      if link:
        node = rsect(*render_type_spec(data, typ))
        return node

      node = rsect(typ.name)
      if data.options.rstMax:
        node['ids'] = ['typereg-type-' + data.options.idEncoder(typ.name)]
        node['target-ids'] = node['ids']
        node['classes']    = ['typereg-type'] + ( typ.meta.classes or [] )
      node.extend(rst2fragments(typ.doc))
      if typ.base == Type.DICT:
        for sub in typ.children:
          node.append(render_type(data, sub))
      return node

    # TODO: implement
    raise NotImplementedError(
      'please open a ticket at https://github.com/cadithealth/pyramid_describe/issues')

  elif isinstance(typ, TypeRef):

    if typ.keys() == ['type']:
      return render_type(data, typ.type, link=link)

    spec = rpara(*render_type_spec(data, typ.type))
    if typ.name and data.options.rstMax:
      spec['classes'] = ['spec']
    for key, value in params.prepare(typ.params, exclude_params=('classes',)):
      spec.append(rtext(', '))
      spec.append(rtext(_(key)))
      if value is None:
        continue
      spec.append(rtext(': '))
      if key == 'default':
        # todo: this will *NOT* be round-trip parseable... fix!
        spec.append(rliteral(value))
      else:
        spec.append(rtext(value))


      # if key != 'default' and value is True:
      #   continue

    if typ.name:
      node = rsect(typ.name)
      if data.options.rstMax:
        node['classes'] = ['attr']
        if typ.params and 'classes' in typ.params:
          node['classes'] += typ.params['classes']
      node.append(spec)
    else:
      node = rsect(spec)

    node.extend(rst2fragments(typ.doc))
    return node

  else:
    raise TypeError('unexpected type for render: %r' % (typ,))

  # TODO: implement
  raise NotImplementedError(
    'please open a ticket at https://github.com/cadithealth/pyramid_describe/issues')

#------------------------------------------------------------------------------
def render_polytype(data, entry, section, poly):
  if not poly:
    return
  if poly.base == Type.COMPOUND and poly.name == Type.ONEOF:
    # todo: what about `poly.doc` (if present)?...
    poly = poly.value
  else:
    poly = [poly]
  types  = [typ.type if isinstance(typ, TypeRef) else typ for typ in poly]
  tnames = [typ.name for typ in types]
  dups   = [x for x, y in collections.Counter(tnames).items() if y > 1]
  if dups:
    raise ValueError(
      'entry %r declared duplicate %s type(s): %r' %
      (entry.dpath, section, dups))
  for idx, typ in enumerate(types):
    node = render_type(data, poly[idx])
    yield (node, typ.name)

#------------------------------------------------------------------------------
def render_typereg(data):
  # todo: perhaps only render types that have at least *something*, e.g.
  #       documentation, attributes, or parameters?...
  types = list(data.types)
  if not types:
    return []
  typereg = rsect(data.options.get('typereg.title') or _('Types'))
  if data.options.rstMax:
    typereg['ids'] = ['section-typereg']
    typereg['target-ids'] = typereg['ids']
    typereg['classes'] = ['typereg']
  for typ in types:
    node = render_type(data, typ, link=False)
    typereg.append(node)
  return [typereg]

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
