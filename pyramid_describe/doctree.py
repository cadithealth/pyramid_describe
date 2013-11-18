# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2013/10/02
# copy: (C) Copyright 2013 Cadit Health Inc., All Rights Reserved.
#------------------------------------------------------------------------------

import yaml
from docutils import utils, nodes, core
from docutils.parsers.rst.directives.html import MetaBody
from pyramid_controllers.util import getVersion

from .i18n import _

#------------------------------------------------------------------------------
def rtitle(text, *args, **kw):
  return nodes.title('', '', text, *args, **kw)
def rpara(*args, **kw):
  return nodes.paragraph('', '', *args, **kw)
def rtext(text, *args, **kw):
  return nodes.Text(text, *args, **kw)
def rsect(title, *args, **kw):
  return nodes.section('', rtitle(rtext(title)), *args, **kw)
def rcont(*args, **kw):
  return nodes.container('', *args, **kw)
Meta = MetaBody('').meta
def rmeta(*args, **kw):
  return Meta('', *args, **kw)

#------------------------------------------------------------------------------
def rst2fragments(text):
  if not text:
    return []
  # todo: this generates error output to STDERR, eg:
  #   <string>:12: (WARNING/2) Inline strong start-string without end-string.
  # it would be *great* if '<string>' were replaced with the actual error
  # source, i.e. controller/method/docstring/etc.

  # TODO: optional failure behaviour: convert the entire
  #       text to a paragraph via:
  #         return [rpara(rtext(text))]
  #       ==> requires error detection.

  return list(core.publish_doctree(text))

# TODO: perhaps all these functions would be much simpler if rstMax was
#       checked once, at exit, and if false, all classes and ids were
#       removed?...

#------------------------------------------------------------------------------
def render(data):
  doc = utils.new_document('<pyramid_describe.document>')
  # todo:
  # doc.settings.text_width = data.options.width

  title = data.options.title or _('Contents of "{}"', data.root)
  if data.options.rstMax:
    doc['title'] = title

  # todo: test this bullet_list stuff (i.e. set showInfo to false)

  mainsect = rsect(rtext(title))
  if data.options.rstMax:
    mainsect['ids'] = ['section-contents']
    mainsect['classes'] = ['contents']

  endpoints = rsect(rtext(data.options.get('endpoints.title') or _('Endpoints')))
  epcont = endpoints
  if data.options.rstMax:
    endpoints['ids'] = ['section-endpoints']
    endpoints['classes'] = ['endpoints']
  if not data.options.showInfo:
    epcont = nodes.bullet_list('', bullet='*')
    endpoints.append(epcont)
  for endpoint in data.endpoints:
    epcont.append(render_entry(data, endpoint))
  mainsect.append(endpoints)

  if data.options.showLegend:
    legend = rsect(rtext(data.options.get('legend.title') or _('Legend')))
    if data.options.rstMax:
      legend['ids'] = ['section-legend']
      legend['classes'] = ['legend']
    for item, desc in data.legend:
      section = rsect(item, rpara(rtext(desc)))
      if data.options.rstMax:
        section['ids'] = ['legend-item-' + data.options.idEncoder(item)]
        section['classes'] = ['legend-item']
      legend.append(section)
    mainsect.append(legend)

  doc.append(mainsect)

  if data.options.showMeta:
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
    doc.append(meta)

  return doc

#------------------------------------------------------------------------------
def render_entry(data, entry):
  if not data.options.showInfo:
    return nodes.list_item('', rpara(rtext(entry.dpath)))
  section = rsect(entry.dpath)
  if data.options.rstMax:
    section['ids'] = [entry.id]
    section['classes'] = ['endpoint']
    if entry.classes:
      section['classes'] += entry.classes
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
      impl = rcont(impl)
      impl['ids'] = ['handler-' + entry.id]
      impl['classes'] = ['handler']
    ret.append(impl)
  ret.extend(rst2fragments(entry.doc))
  ret.extend(render_entry_methods(data, entry))
  ret.extend(render_entry_params(data, entry))
  ret.extend(render_entry_returns(data, entry))
  ret.extend(render_entry_raises(data, entry))
  return ret

#------------------------------------------------------------------------------
def render_entry_methods(data, entry):
  if not data.options.showRest or not entry.methods:
    return []
  section = rsect(_('Methods'))
  if data.options.rstMax:
    section['ids'] = ['methods-' + entry.id]
    section['classes'] = ['methods']
  for meth in entry.methods:
    msect = rsect(meth.method or meth.name)
    if data.options.rstMax:
      msect['ids'] = [meth.id]
      msect['classes'] = ['method']
      if meth.classes:
        msect['classes'] += meth.classes
    msect.extend(render_entry_body(data, meth))
    section.append(msect)
  return [section]

#------------------------------------------------------------------------------
def render_entry_params(data, entry):
  if not entry.params:
    return []
  section = rsect(_('Parameters'))
  if data.options.rstMax:
    section['ids'] = ['params-' + entry.id]
    section['classes'] = ['params']
  for node in entry.params:
    rnode = rsect(node.name)
    if data.options.rstMax:
      rnode['ids'] = ['param-' + entry.id + '-' + data.options.idEncoder(node.name)]
      rnode['classes'] = ['param']
      if node.classes:
        rnode['classes'] += node.classes
    spec = []
    if node.type:
      spec.append(node.type)
    if node.optional:
      spec.append(_('optional'))
    if node.default:
      spec.append(_('default {}', node.default))
    spec = _(', ').join(spec)
    if spec:
      spec = rpara(rtext(spec))
      if data.options.rstMax:
        spec = rcont(spec)
        spec['classes'] = ['spec']
      rnode.append(spec)
    rnode.extend(rst2fragments(node.doc))
    section.append(rnode)
  return [section]

#------------------------------------------------------------------------------
def render_entry_returns(data, entry):
  if not entry.returns:
    return []
  section = rsect(_('Returns'))
  if data.options.rstMax:
    section['ids'] = ['returns-' + entry.id]
    section['classes'] = ['returns']
  for node in entry.returns:
    rnode = rsect(node.type)
    if data.options.rstMax:
      rnode['ids'] = ['return-' + entry.id + '-' + data.options.idEncoder(node.type)]
      rnode['classes'] = ['return']
      if node.classes:
        rnode['classes'] += node.classes
    rnode.extend(rst2fragments(node.doc))
    section.append(rnode)
  return [section]

#------------------------------------------------------------------------------
def render_entry_raises(data, entry):
  if not entry.raises:
    return []
  section = rsect(_('Raises'))
  if data.options.rstMax:
    section['ids'] = ['raises-' + entry.id]
    section['classes'] = ['raises']
  for node in entry.raises:
    rnode = rsect(node.type)
    if data.options.rstMax:
      rnode['ids'] = ['raise-' + entry.id + '-' + data.options.idEncoder(node.type)]
      rnode['classes'] = ['raise']
      if node.classes:
        rnode['classes'] += node.classes
    rnode.extend(rst2fragments(node.doc))
    section.append(rnode)
  return [section]

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
