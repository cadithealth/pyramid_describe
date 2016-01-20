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

.. _`endpoint-2f4954454d5f4944`:

``````````
/{ITEM_ID}
``````````

@PUBLIC

Manages the attributes of the selected item.

.. class:: methods

.. _`methods-endpoint-2f4954454d5f4944`:

:::::::
Methods
:::::::

.. class:: doc-public method

.. _`method-2f4954454d5f4944-504f5354`:

''''''
POST
''''''

@PUBLIC

Alias of :doc.link:`PUT:/{ITEM_ID}`.

.. class:: doc-public method

.. _`method-2f4954454d5f4944-474554`:

''''''
GET
''''''

@PUBLIC

Get the current attributes.

.. class:: returns

.. _`returns-method-2f4954454d5f4944-474554`:

"""""""
Returns
"""""""

.. class:: return

.. _`return-method-2f4954454d5f4944-474554-64696374`:

~~~~~~
dict
~~~~~~

.. class:: attr

^^^^^^
code
^^^^^^

.. class:: spec

string

The short identifier for this item.

.. class:: attr

^^^^^^^^^^^
displayname
^^^^^^^^^^^

.. class:: spec

string

The display name.

.. class:: attr

^^^^^^^
enabled
^^^^^^^

.. class:: spec

boolean

Whether or not this item is available.

.. class:: attr

^^^^^^
area
^^^^^^

.. class:: spec

list(`Shape <#typereg-type-5368617065>`__)

.. class:: attr

^^^^^^^
related
^^^^^^^

.. class:: spec

list(ref)

Related objects.

.. class:: attr

^^^^^^
refs
^^^^^^

.. class:: spec

list(ref(`Shape <#typereg-type-5368617065>`__))

Shapes that reference this item.

.. class:: raises

.. _`raises-method-2f4954454d5f4944-474554`:

""""""
Raises
""""""

.. class:: raise

.. _`raise-method-2f4954454d5f4944-474554-485454504e6f74466f756e64`:

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
`HTTPNotFound <#typereg-type-485454504e6f74466f756e64>`__
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The specified item ID does not exist.

.. class:: doc-public method

.. _`method-2f4954454d5f4944-505554`:

''''''
PUT
''''''

@PUBLIC

Update the item's current attributes.

.. class:: params

.. _`params-method-2f4954454d5f4944-505554`:

""""""""""
Parameters
""""""""""

.. class:: param

.. _`param-method-2f4954454d5f4944-505554-64696374`:

~~~~~~
dict
~~~~~~

.. class:: attr

^^^^^^
code
^^^^^^

.. class:: spec

string

The short identifier for this item.

.. class:: attr

^^^^^^^^^^^
displayname
^^^^^^^^^^^

.. class:: spec

string

The display name.

.. class:: attr

^^^^^^^
enabled
^^^^^^^

.. class:: spec

boolean, default: ``true``

Whether or not this item is available.

.. class:: typereg

.. _`section-typereg`:

------
Types
------

.. class:: source-pyramid-httpexceptions typereg-type

.. _`typereg-type-485454504e6f74466f756e64`:

````````````
HTTPNotFound
````````````

The resource could not be found.

.. class:: attr

::::::
code
::::::

.. class:: spec

``404``

.. class:: attr

:::::::
message
:::::::

.. class:: spec

``"Not Found"``

.. class:: doc-public typereg-type

.. _`typereg-type-5368617065`:

``````
Shape
``````

@PUBLIC

.. class:: attr

::::::
sides
::::::

.. class:: spec

integer
