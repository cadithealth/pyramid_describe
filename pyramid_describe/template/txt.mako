# -*- coding: utf-8 -*-
<%!
import re, textwrap
from pyramid_describe.util import adict
%>\
<%

if data.options.ascii:
  sym = adict(
    blank = '    ',
    down  = '|   ',
    node  = '|-- ',
    last  = '`-- ',
    )
else:
  sym = adict(
    blank = u'    ',
    down  = u'│   ',
    node  = u'├── ',
    last  = u'└── ',
    )

entries = data.tree_entries

for entry in entries:
  cur = ''
  indent = ''
  rparents = list(entry.rparents)
  for c in rparents[1:]:
    indent += sym.blank if c._dlast else sym.down
  if len(rparents) > 0:
    cur += indent + ( sym.last if entry._dlast else sym.node )
    indent += sym.blank if entry._dlast else sym.down
  else:
    cur += indent + data.root
  cur += entry.dname
  folder = ( not entry.isEndpoint and not entry.isMethod ) or \
    len([c for c in entry._dchildren or []
         if not ( c.isRest and not c.isController )]) > 0
  if folder and not cur.endswith('/'):
    cur += '/'
  # cur += ' [' + str(len(entry._dchildren or [])) + ']'
  entry._dline = cur

if data.options.showInfo and len(entries) > 0:
  tlen = max([len(e._dline) for e in entries]) + 3
  if data.options.maxDocColumn and tlen > data.options.maxDocColumn:
    tlen = data.options.maxDocColumn
  # the minus three here is to account for the addition of " # "
  # in the text formatting.
  dlen = data.options.width - tlen - 3
  if data.options.minDocLength and dlen < data.options.minDocLength:
    dlen = data.options.minDocLength
  # force an absolute minimum of 3 characters...
  if dlen >= 3:
    for entry in entries:
      if not entry.doc or not entry._dreal:
        continue
      doc = textwrap.fill(entry.doc, width=data.options.width)
      doc = re.sub(r'\s+', ' ', doc).strip()
      if len(doc) > dlen:
        doc = doc[:dlen - 3] + '...'
      entry._dline = u'{l: <{w}} # {d}'.format(l=entry._dline, w=tlen, d=doc)

%>\
% for entry in entries:
${entry._dline|n}
% endfor
