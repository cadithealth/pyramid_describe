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

.. class:: doc-public endpoint

.. _`endpoint-2f616c6c`:

``````
/all
``````

@PUBLIC

.. class:: returns

.. _`returns-endpoint-2f616c6c`:

:::::::
Returns
:::::::

.. class:: return

.. _`return-endpoint-2f616c6c-64696374`:

''''''
dict
''''''

.. class:: attr

""""""
all
""""""

.. class:: spec

`All <#typereg-type-416c6c>`__

.. class:: doc-public endpoint

.. _`endpoint-2f6974656d73`:

``````
/items
``````

@PUBLIC

Returns the list of items.

.. class:: returns

.. _`returns-endpoint-2f6974656d73`:

:::::::
Returns
:::::::

.. class:: return

.. _`return-endpoint-2f6974656d73-64696374`:

''''''
dict
''''''

.. class:: attr

""""""
items
""""""

.. class:: spec

list(`Item <#typereg-type-4974656d>`__)

A list of `Item` objects.

.. class:: doc-public endpoint

.. _`endpoint-2f706172656e7473`:

````````
/parents
````````

@PUBLIC

Returns the list of parents.

.. class:: returns

.. _`returns-endpoint-2f706172656e7473`:

:::::::
Returns
:::::::

.. class:: return

.. _`return-endpoint-2f706172656e7473-64696374`:

''''''
dict
''''''

.. class:: attr

"""""""
parents
"""""""

.. class:: spec

list(`Parent <#typereg-type-506172656e74>`__)

A list of `Parent` objects.

.. class:: typereg

.. _`section-typereg`:

------
Types
------

.. class:: doc-public typereg-type

.. _`typereg-type-416c6c`:

``````
All
``````

@PUBLIC

.. class:: attr

:::::::
objects
:::::::

.. class:: spec

list(ref)

.. class:: doc-public typereg-type

.. _`typereg-type-4974656d`:

``````
Item
``````

@PUBLIC

.. class:: attr

:::::::
related
:::::::

.. class:: spec

list(ref)

Related objects.

.. class:: attr

:::::::
parents
:::::::

.. class:: spec

list(ref(`Parent <#typereg-type-506172656e74>`__))

This Item's parents.

.. class:: doc-public typereg-type

.. _`typereg-type-506172656e74`:

``````
Parent
``````

@PUBLIC

.. class:: attr

::::::
name
::::::

.. class:: spec

string

The parent's name.

.. class:: attr

::::::
items
::::::

.. class:: spec

list(ref)

A list of this parent's items.
