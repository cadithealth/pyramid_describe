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

#------------------------------------------------------------------------------

# TODO: remove the global-level polution of the `directives` namespace... ugh.

#------------------------------------------------------------------------------
class DocEndpoint(nodes.reference):
  def __init__(self, spec, *args, **kw):
    super(DocEndpoint, self).__init__(*args, **kw)
    self.unmatched = spec.startswith('unmatched:') or spec == 'unmatched'
    if spec == 'unmatched':
      self.cre = re.compile('.*')
    elif spec.startswith('unmatched:') or spec.startswith('regex:'):
      self.cre = re.compile(spec.split(':', 1)[1])
    else:
      self.cre = globre.compile(
        spec if not spec.endswith('/**') else spec[:-3] + '{(/.*)?}',
        flags=globre.EXACT)

# TODO: add rST and HTML serializer of `doc.endpoint` ("just in case")...
#------------------------------------------------------------------------------
class DocEndpointDirective(rst.Directive):
  required_arguments = 1
  # todo:
  #   add `option_spec` parameter such that `unmatched` can be an option...
  #   (and then perhaps the `required_arguments` should be set to 0?):
  #
  #     option_spec = {
  #       'unmatched'  : directives.flag,
  #     }
  #----------------------------------------------------------------------------
  def run(self):
    if not isinstance(self.state, rst.states.Body):
      return [self.state_machine.reporter.error(
        'Invalid context: the "%s" directive can only be used'
        ' as a stand-alone section within the document body.' % (self.name,),
        nodes.literal_block(self.block_text, self.block_text), 
        line=self.lineno)]
    return [DocEndpoint(self.arguments[0])]
directives.register_directive('doc.endpoint', DocEndpointDirective)

#------------------------------------------------------------------------------
def walk(node):
  yield node
  # TODO: should this just be ``for child in node:`` ?
  for child in list(getattr(node, 'children', [])):
    for sub in walk(child):
      yield sub

#------------------------------------------------------------------------------
def render(data, tspec):
  doc = pyramid_render(tspec,
                       dict(data=data, options=data.options),
                       request=data.options.context.request)
  doc = doctree.rst2document(doc, promote=True)
  doc.extend(doctree.render_meta(data, doc.get('title')))
  # todo: confirm that the endpoints are already sorted...
  epstates = [[endpoint, False] for endpoint in data.endpoints]
  for node in walk(doc):
    if isinstance(node, DocEndpoint):
      matched = [epstate
                 for epstate in epstates
                 if ( not epstate[1] or not node.unmatched )
                   and node.cre.search(epstate[0].dpath)]
      for match in matched:
        match[1] = True
      node.replace_self([doctree.render_entry(data, m[0]) for m in matched])
  return doc

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
