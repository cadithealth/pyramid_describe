=========================
Application Documentation
=========================

This document is intended to assist you in using our API. A quote::

  There is nothing in the programming field more despicable than an
  undocumented program.

    -- Edward Yourdon


API Lifecycle
=============

* Beta
* Public
* Deprecated


Endpoints
=========

The available endpoints are broken down into General_ purpose, Item_
specific, and Miscellaneous_ endpoints.


General
-------

General purpose endpoints:

.. doc.endpoint:: /(about)?$
   :regex:


Local Index
```````````

.. doc.endpoint:: /(about)?$
   :regex:
   :link:


Item
----

Endpoints that apply to an ITEM_ID:

.. doc.endpoint:: /{ITEM_ID}(?!/chatter)(/.*)?$
   :regex:


Local Index
```````````

.. doc.endpoint:: /{ITEM_ID}(?!/chatter)(/.*)?$
   :regex:
   :link:


Miscellaneous
-------------

Other:

.. doc.endpoint::
   :unmatched:


Local Index
```````````

.. doc.endpoint::
   :unmatched:
   :link:


Index
=====

.. doc.endpoint::
   :link:


Copyright
=========

See: `http://creativecommons.org/licenses/by/4.0/
<http://creativecommons.org/licenses/by/4.0/>`_.
