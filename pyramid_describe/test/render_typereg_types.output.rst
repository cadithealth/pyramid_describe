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

Triangle

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

````````
Triangle
````````

@PUBLIC

A `Triangle` is a `Shape` with three sides.

::::::
sides
::::::

``3``

:::::::::::
equilateral
:::::::::::

boolean, default: ``true``

Whether or not the sides of this triangle are the same length.

::::::::
examples
::::::::

dict

Just some examples of using parameter examples.

''''''
str
''''''

string, examples: ``"foo"`` | ``"bar"``

''''''
stuff
''''''

any, examples: ``null`` | ``32`` | ``-0.57`` | ``"foo"`` | ``false``
