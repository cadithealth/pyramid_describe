# -*- coding: utf-8 -*-
<%inherit file="pyramid_describe:template/html.mako"/>
<%block name="html_head_pdfkit"></%block>
<%block name="html_style"></%block>
<%block name="html_head_suffix">
 <script language="text/javascript" src="/jquery.min.js"></script>
 <script language="text/javascript">
   $(document).ready(function(){
     alert('hello, world!');
   });
  </script>
</%block>
<%block name="html_body_endpoints">
 <ul class="endpoints">
  % for endpoint in data.endpoints:
   <li>${endpoint.dpath}</li>
  % endfor
 </ul>
</%block>
