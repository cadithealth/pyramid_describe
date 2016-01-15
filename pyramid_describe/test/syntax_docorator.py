from pyramid_controllers import Controller, RestController, expose

class Root(Controller):

  @expose
  def put(self, request):
    '''
    @PUBLIC, @DEPRECATED(2.0.0)

    Some documentation.

    @INTERNAL: Set the `admin` parameter ``True`` to make this item
    admin-only visible.

    @CAPTION Usage Notes
    --------------------

    Some usage notes.

    Another paragraph on that.

    TODO: THIS ENTIRE SECTION IS MISSING IN THE OUTPUT BECAUSE
    NUMPYDOC DOES NOT KNOW ABOUT THIS SECTION... THUS THERE IS A TODO
    TO FIGURE OUT HOW TO LET NUMPYDOC SUPPORT ANY SECTION TITLE...

    :Parameters:

    name : str

      The object name.

      @INTERNAL: the name can be "foo" for an easter egg.

    admin : bool, optional, default: false, @INTERNAL

      Make the item visible to admins only.

    shape : Shape

      @BETA

      A shape.

      @INTERNAL: as generic as possible.

      arg1 : str, @INTERNAL

        first arg.

      arg2 : str

        @INTERNAL

        second arg.

      arg3 : str

        third arg.

        @INTERNAL: also a string.
    '''
