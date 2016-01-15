.. title:: Application Documentation

=========================
Application Documentation
=========================

This document is intended to assist you in using our API. A quote:

::

    There is nothing in the programming field more despicable than an
    undocumented program.
    
      -- Edward Yourdon

-------------
API Lifecycle
-------------

* Beta

* Public

* Deprecated

---------
Endpoints
---------

The available endpoints are broken down into General_ purpose, Item_ specific,
and Miscellaneous_ endpoints.

```````
General
```````

General purpose endpoints:

.. class:: doc-public endpoint

.. _`endpoint-2f`:

::::::
\/
::::::

@PUBLIC

Serves the homepage.

.. class:: doc-public endpoint

.. _`endpoint-2f61626f7574`:

::::::
/about
::::::

@PUBLIC

Serves the glorious "about us" page.

``````
Item
``````

Endpoints that apply to an ITEM_ID:

.. class:: doc-public endpoint

.. _`endpoint-2f4954454d5f4944`:

::::::::::
/{ITEM_ID}
::::::::::

@PUBLIC

Provides RESTful access to the URL-specified item.

.. class:: doc-public endpoint

.. _`endpoint-2f4954454d5f49442f737562616374696f6e`:

::::::::::::::::::::
/{ITEM_ID}/subaction
::::::::::::::::::::

@PUBLIC

Executes a sub-action.

`````````````
Miscellaneous
`````````````

Other:

.. class:: doc-public endpoint

.. _`endpoint-2f4954454d5f49442f63686174746572`:

::::::::::::::::::
/{ITEM_ID}/chatter
::::::::::::::::::

@PUBLIC

Generates chatter.

---------
Copyright
---------

See: `http://creativecommons.org/licenses/by/4.0/
<http://creativecommons.org/licenses/by/4.0/>`_.

.. meta::
    :title: Application Documentation
    :generator: pyramid-describe/{{version}} [format=rst]
    :location: http://localhost/desc?showLegend=false&rstMax=true&showMeta=true
    :pdfkit-margin-bottom: 10mm
    :pdfkit-margin-left: 10mm
    :pdfkit-margin-right: 10mm
    :pdfkit-margin-top: 10mm
