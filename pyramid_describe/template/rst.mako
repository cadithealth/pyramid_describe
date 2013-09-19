# -*- coding: utf-8 -*-
<%!
import textwrap
SECTIONCHARS = '''=-`:'"~^_*+#<>'''
from pyramid_controllers.util import getVersion
def section_title(title, level=0):
  top = level == 0
  level = SECTIONCHARS[level if top else level - 1]
  ret = level * len(title)
  if top:
    ret = [ret, title, ret]
  else:
    ret = [title, ret]
  return '\n'.join(ret)
%>\
##-----------------------------------------------------------------------------
<%block name="rst_body">\
% if data.options.rstMax:
.. title:: ${self.title()|n}

.. class:: endpoints
.. id:: section-endpoints

% endif
${self.rst_title()|n}\
${self.rst_endpoints()|n}\
${self.rst_legend()|n}\
${self.rst_meta()|n}\
</%block>\
##-----------------------------------------------------------------------------
<%def name="title()" filter="trim">
% if data.options.title:
${data.options.title|n}
% else:
Contents of "${data.root|n}"
% endif
</%def>\
##-----------------------------------------------------------------------------
<%def name="rst_title()">\
${section_title(capture(self.title), 0)|n}
</%def>\
##-----------------------------------------------------------------------------
<%def name="rst_endpoints()">\
% for endpoint in data.endpoints:
${self.rst_endpoint(endpoint, 1)|n}\
% endfor
</%def>\
##-----------------------------------------------------------------------------
<%def name="rst_endpoint(entry, level=0)">\
% if data.options.showInfo:
% if data.options.rstMax:

% if entry.classes:
.. class:: endpoint ${' '.join(entry.classes)|n}
% else:
.. class:: endpoint
% endif
.. id:: ${entry.id|n}
% endif

${section_title(entry.dpath, level)|n}
${self.rst_endpoint_body(entry, level=level + 1)|n}\
% else:

* ${entry.dpath|n}
% endif
</%def>\
##-----------------------------------------------------------------------------
<%def name="rst_endpoint_body(entry, level)">\
${self.rst_endpoint_doc(entry, level)|n}\
${self.rst_endpoint_methods(entry, level)|n}\
${self.rst_endpoint_params(entry, level)|n}\
${self.rst_endpoint_returns(entry, level)|n}\
${self.rst_endpoint_raises(entry, level)|n}\
</%def>\
##-----------------------------------------------------------------------------
<%def name="rst_endpoint_doc(entry, level)">\
% if data.options.showImpl and entry.ipath:
% if data.options.rstMax:

.. class:: handler
.. id:: handler-${entry.id|n}
% endif

Handler: ${entry.ipath|n}${'()' if entry.itype == 'instance' else ''|n} [${entry.itype|n}]
% endif
% if data.options.showInfo and entry.doc:

${entry.doc|n}
% endif
</%def>\
##-----------------------------------------------------------------------------
<%def name="rst_endpoint_methods(entry, level)">\
% if data.options.showRest and entry.methods:
% if data.options.rstMax:

.. class:: methods
.. id:: methods-${entry.id|n}
% endif

${section_title('Methods', level)|n}
% for meth in entry.methods:
% if data.options.rstMax:

% if meth.classes:
.. class:: method ${' '.join(meth.classes)|n}
% else:
.. class:: method
% endif
.. id:: ${meth.id|n}
% endif

${section_title('**' + ( meth.method or meth.name ) + '**', level + 1)|n}
${self.rst_endpoint_body(meth, level + 2)|n}\
% endfor
% endif
</%def>\
##-----------------------------------------------------------------------------
<%def name="rst_endpoint_params(entry, level)">\
% if entry.params:
% if data.options.rstMax:

.. class:: params
.. id:: params-${entry.id|n}
% endif

${section_title('Parameters', level)|n}
% for node in entry.params:
<%
spec = node.type or ''
if node.optional:
  spec += ', optional'
if node.default:
  spec += ', default ' + str(node.default)
%>\
% if data.options.rstMax:

.. class:: param
.. id:: param-${entry.id|n}-${data.options.idEncoder(node.name)|n}
% endif

${section_title('**' + node.name + '**', level + 1)|n}
% if data.options.rstMax:

.. class:: spec
% endif

${spec|n}

${node.doc|n}
% endfor
% endif
</%def>\
##-----------------------------------------------------------------------------
<%def name="rst_endpoint_returns(entry, level)">\
% if entry.returns:
% if data.options.rstMax:

.. class:: returns
.. id:: returns-${entry.id|n}
% endif

${section_title('Returns', level)|n}
% for node in entry.returns:
% if data.options.rstMax:

.. class:: return
.. id:: return-${entry.id|n}-${data.options.idEncoder(node.type)|n}
% endif

${section_title('**' + node.type + '**', level + 1)|n}

${node.doc|n}
% endfor
% endif
</%def>\
##-----------------------------------------------------------------------------
<%def name="rst_endpoint_raises(entry, level)">\
% if entry.raises:
% if data.options.rstMax:

.. class:: raises
.. id:: raises-${entry.id|n}
% endif

${section_title('Raises', level)|n}
% for node in entry.raises:
% if data.options.rstMax:

.. class:: raise
.. id:: raise-${entry.id|n}-${data.options.idEncoder(node.type)|n}
% endif

${section_title('**' + node.type + '**', level + 1)|n}

${node.doc|n}
% endfor
% endif
</%def>\
##-----------------------------------------------------------------------------
<%def name="rst_legend()">\
% if data.options.showLegend:
% if data.options.rstMax:

.. class:: legend
.. id:: section-legend
% endif

${section_title('Legend', 0)|n}
% for item, desc in data.legend:
${self.rst_legend_item(item, desc)|n}\
% endfor
% endif
</%def>\
##-----------------------------------------------------------------------------
<%def name="rst_legend_item(item, desc)">\
% if data.options.rstMax:

.. class:: legend-item
.. id:: legend-item-${data.options.idEncoder(item)|n}
% endif

${section_title('`' + item + '`', 1)|n}

${textwrap.fill(desc, width=data.options.width)|n}
</%def>\
##-----------------------------------------------------------------------------
<%def name="rst_generator()" filter="trim">\
<%
gen = None
if data.options.showGenerator:
  gen = 'pyramid-describe'
  if data.options.showGenVersion:
    gen += '/' + getVersion('pyramid_describe')
  gen += ' [format={}]'.format(
    data.options.formats[0] if data.options.formats else 'rst')
%>
${gen or ''|n}
</%def>\
##-----------------------------------------------------------------------------
<%def name="rst_location()" filter="trim">\
<%
loc = None
if data.options.showLocation and data.options.context.request.url:
  loc = data.options.context.request.url
%>
${loc or ''|n}
</%def>\
##-----------------------------------------------------------------------------
<%def name="rst_meta()">\
% if data.options.showMeta:

.. meta::
  :title: ${self.title()|n}
<%
gen = capture(self.rst_generator)
loc = capture(self.rst_location)
%>\
% if gen:
  :generator: ${gen|n}
% endif
% if loc:
  :location: ${loc|n}
% endif
${self.rst_meta_rendering()|n}\
% endif
</%def>\
##-----------------------------------------------------------------------------
<%def name="rst_meta_rendering()">\
% if data.options.rstMax and data.options.rstPdfkit:
  :pdfkit-page-size: ${data.options.pageSize|n}
  :pdfkit-orientation: ${data.options.pageOrientation|n}
% if not data.options.showOutline:
  :pdfkit-no-outline:
% endif
  :pdfkit-margin-top: ${data.options.pageMarginTop|n}
  :pdfkit-margin-right: ${data.options.pageMarginRight|n}
  :pdfkit-margin-bottom: ${data.options.pageMarginBottom|n}
  :pdfkit-margin-left: ${data.options.pageMarginLeft|n}
% if data.options.pageGrayscale:
  :pdfkit-grayscale:
% endif
##  :pdfkit-print-media-type: 
##  :pdfkit-disable-plugins: 
##  :pdfkit-zoom: 1.0
##  :pdfkit-javascript-delay: 1000
##  :pdfkit-disable-javascript: 
% endif
</%def>\
##-----------------------------------------------------------------------------
