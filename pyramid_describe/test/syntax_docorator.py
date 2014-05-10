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

    admin : bool, optional, default: false, @INTERNAL

      Make the item visible to admins only.
    '''
