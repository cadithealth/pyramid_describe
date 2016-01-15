===============
Contents of "/"
===============

---------
Endpoints
---------

``````
\/
``````

:::::::
Methods
:::::::

''''''
POST
''''''

@PUBLIC

Create a new shape.

""""""""""
Parameters
""""""""""

~~~~~~
dict
~~~~~~

^^^^^^
shape
^^^^^^

Shape

The new shape to create.

"""""""
Returns
"""""""

~~~~~~
dict
~~~~~~

^^^^^^
shape
^^^^^^

Shape

''''''
GET
''''''

@PUBLIC

Get a list of all currently registered shapes.

"""""""
Returns
"""""""

~~~~~~
dict
~~~~~~

^^^^^^
shapes
^^^^^^

Shape

`````````
/favorite
`````````

@PUBLIC

:::::::
Returns
:::::::

''''''
dict
''''''

""""""
shape
""""""

N/A

------
Types
------

``````
Shape
``````

@PUBLIC

A `Shape` is a polygon with three or more sides.

:::::::
created
:::::::

number, read-only

The epoch timestamp that this shape was created.

::::::
sides
::::::

integer

The number of sides this shape has.
