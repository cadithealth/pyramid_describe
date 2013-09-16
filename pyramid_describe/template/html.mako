# -*- coding: utf-8 -*-
<%!
from pyramid_controllers.util import getVersion
%>\
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" lang="en" xml:lang="en">
 <head>
  <%block name="html_head">
   <%block name="html_head_prefix"></%block>
   <title><%block name="html_head_title"><%block name="html_title">Contents of "${data.root|h}"</%block></%block></title>
   <meta http-equiv="content-type" content="text/html; charset=UTF-8"/>
   <meta name="generator" content="pyramid-describe/${getVersion('pyramid_describe')|h}"/>
   <%block name="html_head_pdfkit">
    <meta name="pdfkit-page-size" content="${data.options.pageSize}"/>
    <meta name="pdfkit-orientation" content="${data.options.pageOrientation}"/>
    % if not data.options.showOutline:
     <meta name="pdfkit-no-outline" content=""/>
    % endif
    <meta name="pdfkit-margin-top" content="${data.options.pageMarginTop}"/>
    <meta name="pdfkit-margin-right" content="${data.options.pageMarginRight}"/>
    <meta name="pdfkit-margin-bottom" content="${data.options.pageMarginBottom}"/>
    <meta name="pdfkit-margin-left" content="${data.options.pageMarginLeft}"/>
    % if data.options.pageGrayscale:
     <meta name="pdfkit-grayscale" content=""/>
    % endif
    ## <meta name="pdfkit-print-media-type" content=""/>
    ## <meta name="pdfkit-disable-plugins" content=""/>
    ## <meta name="pdfkit-zoom" content="1.0"/>
    ## <meta name="pdfkit-javascript-delay" content="1000"/>
    ## <meta name="pdfkit-disable-javascript" content=""/>
   </%block>
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
 <body id="<%block name="html_body_id"></%block>" class="<%block name="html_body_class"></%block>">
  <%block name="html_body">
   <%block name="html_body_prefix"></%block>
   <h1><%block name="html_body_title">${self.html_title()}</%block></h1>
   <%block name="html_body_endpoints">
    <dl class="endpoints">
     % for endpoint in data.endpoints:
      <%def name="html_body_endpoint(endpoint)">
       <dt id="${endpoint.id}"><h2>${endpoint.dpath}</h2></dt>
       <dd>
        ## TODO: if `html_body_endpoint_doc` generates no data, output "(Undocumented.)"
        ${html_body_endpoint_doc(endpoint, level=2)}
       </dd>
      </%def>
      <%def name="html_body_endpoint_doc(entry, level)">
       % if entry.doc:
        <p>${entry.doc}</p>
       % endif
       % if entry.params:
        <h${level + 1}>Parameters</h${level + 1}>
        <dl class="params">
         % for param in entry.params:
          <dt id="${param.id}"><h${level + 2}>${param.name or ''}</h${level + 2}></dt>
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
        <h${level + 1}>Returns</h${level + 1}>
        <dl class="returns">
         % for node in entry.returns:
          <dt id="${node.id}"><h${level + 2}>${node.type or ''}</h${level + 2}></dt>
          <dd>
           % if node.doc:
            <p>${node.doc}</p>
           % endif
          </dd>
         % endfor
        </dl>
       % endif
       % if entry.raises:
        <h${level + 1}>Raises</h${level + 1}>
        <dl class="raises">
         % for node in entry.raises:
          <dt id="${node.id}"><h${level + 2}>${node.type or ''}</h${level + 2}></dt>
          <dd>
           % if node.doc:
            <p>${node.doc}</p>
           % endif
          </dd>
         % endfor
        </dl>
       % endif
       % if entry.methods:
        <h${level + 1}>Supported Methods</h${level + 1}>
        <dl class="methods">
         % for meth in entry.methods:
          <dt id="${meth.id}"><h${level + 2}>${meth.method or meth.name or ''}</h${level + 2}></dt>
          <dd>
           ${html_body_endpoint_doc(meth, level=level + 2)}
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
     <h1 class="legend">Legend</h1>
     <dl class="legend">
      % for item, desc in data.legend:
       <%def name="html_body_legend_entry(item, desc)">
        <dt><h2>${item}</h2></dt>
        <dd><p>${desc}</p></dd>
       </%def>
       ${html_body_legend_entry(item, desc)}
      % endfor
     </dl>
    </%block>
   % endif
   <%block name="html_body_suffix"></%block>
  </%block>
 </body>
</html>
