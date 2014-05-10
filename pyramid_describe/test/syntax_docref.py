from pyramid_controllers import Controller, RestController, expose

class ItemController(RestController):

  '''
  Manages the attributes of the selected item.
  '''

  @expose
  def get(self, request):
    '''
    Get the current attributes.
    
    Returns
    -------
    
    JSON data.
    '''

  @expose
  def put(self, request):
    '''
    Update the item's current attributes.
    
    :doc.copy:`GET:.:Returns,Raises`
    '''

  @expose
  def post(self, request):
    '''
    Alias of :doc.link:`PUT:.`.
    
    :doc.copy:`PUT:.`
    '''

class Root(Controller):

  ITEM_ID = ItemController(expose=False)
