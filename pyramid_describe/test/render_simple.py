from pyramid_controllers import Controller, RestController, expose, index

class ItemController(RestController):
  'Provides RESTful access to the URL-specified item.'

  def not_exposed(self, *args, **kw):
    'This should not be reachable.'

  @expose
  def subaction(self, request):
    'Executes a sub-action.'

  @expose
  def chatter(self, request):
    'Generates chatter.'

class Root(Controller):
  'Application root.'

  ITEM_ID = ItemController(expose=False)

  @index
  def index(self, request):
    'Serves the homepage.'

  @expose
  def about(self, request):
    'Serves the glorious "about us" page.'
