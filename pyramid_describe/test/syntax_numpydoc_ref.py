from pyramid_controllers import Controller, RestController, expose

class Root(Controller):

  #----------------------------------------------------------------------------
  # TODO: the TypeRegistry **should** support this kind of recursive
  #       referencing...
  # @expose
  # def get(self, request):
  #   '''
  #   @PUBLIC
  #
  #   Returns the attributes of the specified `Item` object.
  #
  #   :Returns:
  #
  #   item : Item
  #     @PUBLIC
  #     related : list(ref)
  #       Related objects.
  #     parents : list(ref(Item))
  #       This Item's parents.
  #   '''
  # /TODO
  #----------------------------------------------------------------------------

  @expose
  def all(self, request):
    '''
    @PUBLIC

    :Returns:

    all : All

      @PUBLIC

      objects : list(ref)
    '''

  @expose
  def items(self, request):
    '''
    @PUBLIC

    Returns the list of items.

    :Returns:

    items : list(Item)
      A list of `Item` objects.

      Item
        @PUBLIC

        related : list(ref)
          Related objects.
        parents : list(ref(Parent))
          This Item's parents.
    '''

  @expose
  def parents(self, request):
    '''
    @PUBLIC

    Returns the list of parents.

    :Returns:

    parents : list(Parent)
      A list of `Parent` objects.

      Parent
        @PUBLIC

        name : str
          The parent's name.
        items : list(ref)
          A list of this parent's items.
    '''
  # TODO: the TypeRegistry **should** support this kind of cyclical
  #       referencing, where `Parent.items` above is defined as:
  #
  #      items : list(ref(Item))
  #        A list of this parent's items.
