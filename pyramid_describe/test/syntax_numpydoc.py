from pyramid_controllers import Controller, RestController, expose

class Item(RestController):

  '''
  @PUBLIC

  Manages the attributes of the selected item.
  '''

  @expose
  def get(self, request):
    '''
    @PUBLIC

    Get the current attributes.

    :Returns:

    dict

      code : str

        The short identifier for this item.

      displayname : str

        The display name.

      enabled : bool

        Whether or not this item is available.

      area : list(Shape)

        Shape

          @PUBLIC

          sides : int

      related : list(ref)

        Related objects.

      refs : list(ref(Shape))

        Shapes that reference this item.

    :Raises:

    HTTPNotFound

      The specified item ID does not exist.
    '''

  @expose
  def put(self, request):
    '''
    @PUBLIC

    Update the item's current attributes.

    :Parameters:

    code : str

      The short identifier for this item.

    displayname : str

      The display name.

    enabled : bool, optional, default: true

      Whether or not this item is available.

    '''

  @expose
  def post(self, request):
    '''
    @PUBLIC

    Alias of :doc.link:`PUT:.`.
    '''

class Root(Controller):

  ITEM_ID = Item(expose=False)
