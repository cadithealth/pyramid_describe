from pyramid_controllers import Controller, RestController, expose

def item_get_doc_callable_abs(): return 'Get'
def item_get_doc_callable_rel(): return 'the'
def item_get_doc_callable_uprel(): return 'current'
item_get_doc_string = 'attributes.'

class ItemController(RestController):

  '''
  :doc.import:`./syntax_docref_import_abs.rst`
  :doc.import:`./syntax_docref_import_rel.rst`
  '''

  @expose
  def get(self, request):
    '''
    :doc.import:`pyramid_describe.test.syntax_docref.item_get_doc_callable_abs`
    :doc.import:`.syntax_docref.item_get_doc_callable_rel`
    :doc.import:`..test.syntax_docref.item_get_doc_callable_uprel`
    :doc.import:`pyramid_describe.test.syntax_docref.item_get_doc_string`

    Returns
    -------

    JSON data.
    '''

  @expose
  def put(self, request):
    '''
    Update the item's current attributes.

    :doc.copy:`GET:.:Returns`
    '''

  @expose
  def post(self, request):
    '''
    Alias of :doc.link:`PUT:.`.

    :doc.copy:`PUT:.`
    '''

class Root(Controller):

  ITEM_ID = ItemController(expose=False)
