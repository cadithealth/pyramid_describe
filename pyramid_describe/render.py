# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2014/05/13
# copy: (C) Copyright 2014-EOT Cadit Inc., All Rights Reserved.
#------------------------------------------------------------------------------

import re
from pyramid.renderers import render as pyramid_render
from docutils import nodes
from docutils.parsers import rst
from docutils.parsers.rst import directives#, roles
import globre

from . import doctree
from .i18n import _
from .syntax.docref import pyrdesc_doc_link as doc_link

#------------------------------------------------------------------------------

# TODO: remove the global-level polution of the `directives` namespace... ugh.

#------------------------------------------------------------------------------
class DocEndpoint(nodes.reference):
  def __init__(self, spec, regex=False, unmatched=False, link=False, *args, **kw):
    super(DocEndpoint, self).__init__(*args, **kw)
    self.unmatched = unmatched
    self.link      = link
    if spec is None:
      self.cre = re.compile('.*')
    else:
      if regex:
        self.cre = re.compile(spec)
      else:
        self.cre = globre.compile(
          spec if not spec.endswith('/**') else spec[:-3] + '{(/.*)?}',
          flags=globre.EXACT)

# TODO: add rST and HTML serializer of `doc.endpoint` ("just in case")...
#------------------------------------------------------------------------------
class DocEndpointDirective(rst.Directive):
  # TODO: make DocEndpointDirective (and DocEndpoint) support multiple
  #       arguments, which are OR'ed together.
  optional_arguments = 1
  option_spec = {
    'unmatched'  : directives.flag,
    'regex'      : directives.flag,
    'link'       : directives.flag,
  }
  #----------------------------------------------------------------------------
  def run(self):
    if not isinstance(self.state, rst.states.Body):
      return [self.state_machine.reporter.error(
        'Invalid context: the "%s" directive can only be used'
        ' as a stand-alone section within the document body.' % (self.name,),
        nodes.literal_block(self.block_text, self.block_text), 
        line=self.lineno)]
    spec = self.arguments[0] if len(self.arguments) > 0 else None
    # for some retarded reason, when a flag is specified, it returns
    # ``None``... so, converting that here.
    opts = dict(self.options)
    for key, val in list(opts.items()):
      if val is None:
        opts[key] = True
    return [DocEndpoint(spec, **opts)]
directives.register_directive('doc.endpoint', DocEndpointDirective)

#------------------------------------------------------------------------------
def renderDocEndpoint(data, node, endpoints):
  if not node.link:
    node.replace_self([doctree.render_entry(data, ep) for ep in endpoints])
    return
  # todo: to be "correct", this `repl` should be a nodes.bullet_list...
  #       but the problem with that is that then two consecutive lists
  #       will be technically not part of the same list.
  #       ==> NOTE: by makeing DocEndpoint accept multiple spec's, this
  #           would be made a non-issue...
  repl = []
  for endpoint in endpoints:
    repl.append(nodes.list_item('', doctree.rpara(
      doc_link('', doctree.rtext(endpoint.dpath))
    )))
  node.replace_self(repl)

#------------------------------------------------------------------------------
def render(data, tspec):
  doc = pyramid_render(tspec,
                       dict(data=data, options=data.options),
                       request=data.options.context.request)
  doc = doctree.rst2document(doc, promote=True)
  doc.extend(doctree.render_meta(data, doc.get('title')))
  # todo: perhaps move this sorting into `describe.py`
  #       ==> and make sorting configurable
  epstates = sorted([[endpoint, False] for endpoint in data.endpoints],
                    key=lambda entry: entry[0].path.lower())
  for node in doctree.walk(doc):
    if isinstance(node, DocEndpoint):
      matched = [epstate
                 for epstate in epstates
                 if ( not epstate[1] or not node.unmatched )
                   and node.cre.search(epstate[0].dpath)]
      for match in matched:
        match[1] = True
      renderDocEndpoint(data, node, [m[0] for m in matched])
  return doc

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
