Contents of "/"
***************

/
=

  The application root.

/contact
========

  Contact manager.

  Supported Methods
  -----------------

  * **POST**:

    Creates a new 'contact' object.

/contact/{CONTACTID}
====================

  RESTful access to a specific contact.

  Supported Methods
  -----------------

  * **DELETE**:

    Delete this contact.

  * **GET**:

    Get this contact's details.

  * **PUT**:

    Update this contact's details.

/login
======

  Authenticate against the server.

/logout
=======

  Remove authentication tokens.

Legend
******

  * `{NAME}`:

    Placeholder -- usually replaced with an ID or other identifier of a RESTful
    object.

  * `<NAME>`:

    Not an actual endpoint, but the HTTP method to use.

  * `NAME/?`:

    Dynamically evaluated endpoint; no further information can be determined
    without request-specific details.

  * `*`:

    This endpoint is a `default` handler, and is therefore free to interpret
    path arguments dynamically; no further information can be determined
    without request-specific details.

  * `...`:

    This endpoint is a `lookup` handler, and is therefore free to interpret
    path arguments dynamically; no further information can be determined
    without request-specific details.

.. generator: pyramid-describe/0.1.16 [format=rst]
.. location: http://localhost/
