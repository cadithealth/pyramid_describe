from pyramid_controllers import Controller, RestController, expose, index

class ItemController(RestController):
  '''
  @PUBLIC

  Provides RESTful access to the URL-specified item.
  '''

  def not_exposed(self, *args, **kw):
    '''
    @PUBLIC

    This should not be reachable.
    '''

  @expose
  def subaction(self, request):
    '''
    @PUBLIC

    Executes a sub-action.
    '''

  @expose
  def chatter(self, request):
    '''
    @PUBLIC

    Generates chatter.
    '''

class Root(Controller):
  '''
  @PUBLIC

  Application root.
  '''

  ITEM_ID = ItemController(expose=False)

  @index
  def index(self, request):
    '''
    @PUBLIC

    Serves the homepage.
    '''

  @expose
  def about(self, request):
    '''
    @PUBLIC

    Serves the glorious "about us" page.
    '''
