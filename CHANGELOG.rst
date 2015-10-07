=========
ChangeLog
=========


v0.4.6
======

* Removed `distribute` dependency


v0.4.5
======

* Added support for reStructuredText admonitions (attention, caution,
  danger, error, hint, important, note, tip, warning)
* Fixed reStructuredText text wrapping of hyphenated words


v0.4.4
======

* Added support for reStructuredText enumerated (numbered) lists


v0.4.3
======

* Corrected `figure` override attributes


v0.4.2
======

* Added support for `image` and `figure` directives
* Added documentation on aliasing doc.* directives


v0.4.1
======

* Modified display of controller methods to be sorted first
  semantically, then alphabetically (with customizability)
* "doc.endpoint :link:" directives now use separate "matched" flag


v0.4.0
======

* Added anonymous hyperlink support in the reStructuredText writer
* Added support for endpoint link listings


v0.3.3
======

* Added support for classes on tables in the reStructuredText writer


v0.3.2
======

* Moved ``.. doc.endpoint:: PATH`` to use GLOB-based matching instead
  of plain strings


v0.3.1
======

* Added support to control assembly of endpoints into one document via
  pyramid template rendering with new ``describe.render.template``
  option


v0.2.0
======

* Added workaround for setting ``describe.inspect`` so that it works
  (but in a non-ideal way)
* Added some common rST text roles with aliasing to "literal" (class,
  meth, func)
* Added useful rST text roles for interlinking documentation
  (doc.link, doc.copy, doc.import)
* Added numpydoc as default filtering of documentation
* Split parsing responsibilities of ``entries.filters`` into separate
  option ``entries.parsers`` (in preparation for caching optimization)


v0.1.35
=======

* Improved handling of targetable node IDs in rST writer


v0.1.34
=======

* Moved to open-ended configuration of `pdfkit` options
* Added "stop-gap" catch for failed PDF rendering
* Added work-around for single-character meta content


v0.1.32
=======

* Restructured doctree to include global "main" section


v0.1.31
=======

* Added support for implicit target references
* Added unicode character support for PDF generation


v0.1.30
=======

* Added "rst2rst.py" script
* Added substitution support (for rST writer)
* Improved separation token serialization (for rST writer)
* Corrected reStructuredText section title rendering
* Corrected DocTree structure (switch "container" to "section" node)
* Removed non-matching extensions from manifest


v0.1.28
=======

* Added suppression of lone-section collapsing into document
* Added support for `format.rst.filters` option
* Small improvement to rST output writer (text escaping)
* Added support for inline email addresses in rST writer


v0.1.27
=======

* First tagged release
