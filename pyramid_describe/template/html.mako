# -*- coding: utf-8 -*-
<%!
from pyramid_controllers.util import getVersion
%>\
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" lang="en" xml:lang="en">
 <head>
  <%block name="html_head">
   <%block name="html_head_prefix"></%block>
   <title><%block name="html_head_title">Contents of "${data.root|h}"</%block></title>
   <meta http-equiv="content-type" content="text/html; charset=UTF-8"/>
   <meta name="generator" content="pyramid-describe/${getVersion('pyramid_describe')|h}"/>
   <style type="text/css">
    <%block name="html_style">
     dl{margin-left: 2em;}
     dt{font-weight: bold;}
     dd{margin:0.5em 0 0.75em 2em;}
     .params .param-spec{font-style: italic;}
    </%block>
   </style>
   <%block name="html_head_suffix"></%block>
  </%block>
 </head>
 <body>
  <%block name="html_body">
   <h1><%block name="html_body_title">Contents of "${data.root|h}"</%block></h1>
   <%block name="html_body_endpoints">
    <dl class="endpoints">
     % for endpoint in data.endpoints:
      <%def name="html_body_endpoint(endpoint)">
       <dt id="${endpoint.id}">${endpoint.dpath}</dt>
       <dd>
        ## TODO: if `html_body_endpoint_doc` generates no data, output "(Undocumented.)"
        ${html_body_endpoint_doc(endpoint)}
       </dd>
      </%def>
      <%def name="html_body_endpoint_doc(entry)">
       % if entry.doc:
        <p>${entry.doc}</p>
       % endif
       % if entry.params:
        <h4>Parameters</h4>
        <dl class="params">
         % for param in entry.params:
          <dt id="${param.id}">${param.name or ''}</dt>
          <dd>
           <div class="param-spec">${param.type or ''
            }${', optional' if param.optional else ''
            }${( ', default ' + str(param.default) ) if param.default else ''
            }</div>
           % if param.doc:
            <p>${param.doc}</p>
           % endif
          </dd>
         % endfor
        </dl>
       % endif
       % if entry.returns:
        <h4>Returns</h4>
        <dl class="returns">
         % for node in entry.returns:
          <dt id="${node.id}">${node.type or ''}</dt>
          <dd>
           % if node.doc:
            <p>${node.doc}</p>
           % endif
          </dd>
         % endfor
        </dl>
       % endif
       % if entry.raises:
        <h4>Raises</h4>
        <dl class="raises">
         % for node in entry.raises:
          <dt id="${node.id}">${node.type or ''}</dt>
          <dd>
           % if node.doc:
            <p>${node.doc}</p>
           % endif
          </dd>
         % endfor
        </dl>
       % endif
       % if entry.methods:
        <h3>Supported Methods</h3>
        <dl class="methods">
         % for meth in entry.methods:
          <dt id="${meth.id}">${meth.method or meth.name or ''}</dt>
          <dd>
           ${html_body_endpoint_doc(meth)}
          </dd>
         % endfor
        </dl>
       % endif
      </%def>
      ${html_body_endpoint(endpoint)}
     % endfor
    </dl>
   </%block>
   % if data.options.showLegend and data.legend:
    <%block name="html_body_legend">
     <h3>Legend</h3>
     <dl class="legend">
      % for item, desc in data.legend:
       <%def name="html_body_legend_entry(item, desc)">
        <dt>${item}</dt>
        <dd><p>${desc}</p></dd>
       </%def>
       ${html_body_legend_entry(item, desc)}
      % endfor
     </dl>
    </%block>
   % endif
  </%block>
 </body>
</html>
