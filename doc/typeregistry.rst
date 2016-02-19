=============
Type Registry
=============

Pyramid-describe has a type management facility that is primarily
geared at documenting parameters (no surprise there). To accomplish
that the Describer has a type registry, and each parameter defined in
the described interface can specify both a datatype (which references
the types declared in the type registry) and qualifiers associated
with that parameter.

For example, the following declares the `rating` parameter that is an
integer, and qualifies that it is nullable, write-only, and must be in
the range of 0 to 10. It also specifies examples and default
values:

.. code:: text

  rating : integer, nullable, write-only, min: 0, max: 10, example: 5, default: null


Datatypes
=========

The datatypes supported by pyramid-describe are the standard primitive
datatypes, a few compound types, and dictionary-based complex types
(i.e. dictionaries with defined entry names).

The primitive types:

* null
* boolean
* integer
* number
* byte
* bytes
* string

The compound and meta types:

* list
* dict
* enum (i.e. "one-of" -- primarily used for validation)
* union (i.e. "all-of" -- primarily used for validation)
* any (i.e. any datatype -- ``void*`` in C/C++ terminology)
* ref (i.e. a Reference object)
* constant

Pyramid-describe also supports a limited ability to define complex
types beyond the above known types, but this is currently limited to
extending the `dict` type to have a description and declared
attributes that in turn can specify datatypes and qualifiers. For
example, the following defines a "Shape" datatype that has a
description and two attributes, "sides" to be the number of sides and
a "name":

.. code:: text

  Shape

    A two-dimensional regular (i.e. all sides have the same length)
    polygon.

    sides : int, min: 3

      The number of sides this shape has.    

    name : str, example: "Triangle", default: null

      The name, if specified, of this kind of shape.


Qualifiers
==========

The pyramid-describe package supports any arbitrary qualifiers
associated with a parameter's datatype. Qualifiers must be simple
names; i.e. are limited to the similar restrictions place on symbol
names in most programming languages, with the addition of the dash
character ("-"). Qualifiers can be either flags (i.e. present or not
present) or have values, which can be anything (with the restrictions
presented below for known types and parsing rules).

With the exception of the `example` qualifier, qualifiers cannot be
specified multiple times.

The following is a list of known qualifiers and their meaning:

* optional

* required (opposite of, and gets merged into, `optional`)

* read (or "r", indicates this field is readable)

* write (or "w", indicates this field is writable)

* create (or "c", indicates this field is writable-on-create)

* read-only (or "ro")

* write-only (or "wo")

* create-only (or "co")

* nullable

* example (free-form example, can be specified multiple times)

* examples (JSON example value, can use "one-of" syntax)

* default (JSON default value)

* default-to (free-form version of `default`)
