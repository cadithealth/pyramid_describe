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

.. class:: endpoint

.. _`endpoint-2f4954454d5f4944`:

``````````
/{ITEM_ID}
``````````

Manages the attributes of the selected item.

.. class:: methods

.. _`methods-endpoint-2f4954454d5f4944`:

:::::::
Methods
:::::::

.. class:: method

.. _`method-2f4954454d5f4944-504f5354`:

''''''
POST
''''''

Alias of :doc.link:`PUT:/{ITEM_ID}`.

.. class:: method

.. _`method-2f4954454d5f4944-474554`:

''''''
GET
''''''

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

str

The short identifier for this item.

.. class:: attr

^^^^^^^^^^^
displayname
^^^^^^^^^^^

.. class:: spec

str

The display name.

.. class:: attr

^^^^^^^
enabled
^^^^^^^

.. class:: spec

bool

Whether or not this item is available.

.. class:: raises

.. _`raises-method-2f4954454d5f4944-474554`:

""""""
Raises
""""""

.. class:: raise

.. _`raise-method-2f4954454d5f4944-474554-485454504e6f74466f756e64`:

~~~~~~~~~~~~
HTTPNotFound
~~~~~~~~~~~~

The specified item ID does not exist.

.. class:: method

.. _`method-2f4954454d5f4944-505554`:

''''''
PUT
''''''

Update the item's current attributes.

.. class:: params

.. _`params-method-2f4954454d5f4944-505554`:

""""""""""
Parameters
""""""""""

.. class:: param

.. _`param-method-2f4954454d5f4944-505554-636f6465`:

~~~~~~
code
~~~~~~

.. class:: spec

str

The short identifier for this item.

.. class:: param

.. _`param-method-2f4954454d5f4944-505554-646973706c61796e616d65`:

~~~~~~~~~~~
displayname
~~~~~~~~~~~

.. class:: spec

str

The display name.

.. class:: param

.. _`param-method-2f4954454d5f4944-505554-656e61626c6564`:

~~~~~~~
enabled
~~~~~~~

.. class:: spec

bool, optional, default: true

Whether or not this item is available.
