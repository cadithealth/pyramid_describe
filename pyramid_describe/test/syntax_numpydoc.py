from pyramid_controllers import Controller, RestController, expose

class Item(RestController):

  '''
  Manages the attributes of the selected item.
  '''

  @expose
  def get(self, request):
    '''
    Get the current attributes.

    :Returns:

    dict

      code : str

        The short identifier for this item.

      displayname : str

        The display name.

      enabled : bool

        Whether or not this item is available.

    :Raises:

    HTTPNotFound

      The specified item ID does not exist.
    '''

  @expose
  def put(self, request):
    '''
    Update the item's current attributes.

    :Parameters:

    code : str

      The short identifier for this item.

    displayname : str

      The display name.

    enabled : bool, optional, default: true

      Whether or not this item is available.

    :doc.copy:`GET:.:Returns,Raises`
    '''

  @expose
  def post(self, request):
    '''
    Alias of :doc.link:`PUT:.`.

    :doc.copy:`PUT:.`
    '''

class Root(Controller):

  ITEM_ID = Item(expose=False)
