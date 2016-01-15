.. title:: Contents of "/"

.. class:: contents

.. _`section-contents`:

===============
Contents of "/"
===============

.. class:: endpoints

.. _`section-endpoints`:

---------
Endpoints
---------

.. class:: doc-deprecated doc-deprecated-2-0-0 doc-public endpoint

.. _`endpoint-2f707574`:

``````
/put
``````

@PUBLIC, @DEPRECATED(2.0.0)

Some documentation.

.. class:: doc-internal

@INTERNAL: Set the `admin` parameter ``True`` to make this item admin-only
visible.

.. class:: params

.. _`params-endpoint-2f707574`:

::::::::::
Parameters
::::::::::

.. class:: param

.. _`param-endpoint-2f707574-64696374`:

''''''
dict
''''''

.. class:: attr

""""""
name
""""""

.. class:: spec

string

The object name.

.. class:: doc-internal

@INTERNAL: the name can be "foo" for an easter egg.

.. class:: attr doc-internal

""""""
admin
""""""

.. class:: spec

boolean, @INTERNAL, default: ``false``

Make the item visible to admins only.

.. class:: attr

""""""
shape
""""""

.. class:: spec

`Shape <#typereg-type-5368617065>`__

.. class:: typereg

.. _`section-typereg`:

------
Types
------

.. class:: doc-beta typereg-type

.. _`typereg-type-5368617065`:

``````
Shape
``````

@BETA

A shape.

.. class:: doc-internal

@INTERNAL: as generic as possible.

.. class:: attr doc-internal

::::::
arg1
::::::

.. class:: spec

string, @INTERNAL

first arg.

.. class:: attr doc-internal

::::::
arg2
::::::

.. class:: spec

string, @INTERNAL

@INTERNAL

second arg.

.. class:: attr

::::::
arg3
::::::

.. class:: spec

string

third arg.

.. class:: doc-internal

@INTERNAL: also a string.
