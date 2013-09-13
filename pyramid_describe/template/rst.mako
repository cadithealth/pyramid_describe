# -*- coding: utf-8 -*-
<%!
import textwrap
from pyramid_controllers.util import getVersion
def section_title(title, level='='):
  return title + '\n' + ( level * len(title) )
def indent(text):
  return text.replace('\n', '\n  ').replace('\n  \n', '\n\n')
%>\
<%block name="rst_title">\
${section_title('Contents of "' + data.root + '"', '*')|n}

</%block>\
<%block name="rst_endpoints">\
% for endpoint in data.endpoints:
${rst_endpoint(endpoint)}
% endfor
</%block>\
<%def name="rst_endpoint(entry)">\
${section_title(entry.dpath, '=')|n}

  ${rst_endpoint_doc(entry)}
</%def>\
<%def name="rst_endpoint_doc(entry)" filter="indent, trim">\
% if data.options.showImpl and entry.ipath:
Handler: ${entry.ipath|n}${'()' if entry.itype == 'instance' else ''|n} [${entry.itype|n}]

% endif
% if data.options.showInfo and entry.doc:
${entry.doc|n}
% if entry.params:

:Parameters:
% for node in entry.params:
<%
spec = node.type or ''
if node.optional:
  spec += ', optional'
if node.default:
  spec += ', default ' + str(node.default)
%>\

**${node.name|n}** : ${spec|n}

  ${node.doc|n,indent}
% endfor
% endif
% if entry.returns:

:Returns:
% for node in entry.returns:

**${node.type|n}**

  ${node.doc|n,indent}
% endfor
% endif
% if entry.raises:

:Raises:
% for node in entry.raises:

**${node.type|n}**

  ${node.doc|n,indent}
% endfor
% endif
% if data.options.showRest and entry.methods:

Supported Methods
-----------------

% for meth in entry.methods:
% if meth.doc:
* **${meth.method or meth.name or ''|n}**:

  ${rst_endpoint_doc(meth)}

% else:
* **${meth.method or meth.name or ''|n}**

% endif
% endfor
% endif
% endif
</%def>\
% if data.options.showLegend:
<%block name="rst_legend">\
Legend
******

% for item, desc in data.legend:
  * `${item|n}`:

    ${textwrap.fill(desc, width=data.options.width - 4)|n,indent,indent}

% endfor
</%block>\
% endif
% if data.options.showGenerator:
<%block name="rst_generator">\
<%
ver = ''
if data.options.showGenVersion:
  ver += '/' + getVersion('pyramid_describe')
%>\
.. generator: pyramid-describe${ver|n} [format=rst]
</%block>\
% endif
% if data.options.showLocation and data.options.request.url:
<%block name="rst_location">\
.. location: ${data.options.request.url|n}
</%block>\
% endif
