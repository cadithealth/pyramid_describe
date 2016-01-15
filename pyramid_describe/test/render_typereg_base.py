from pyramid_controllers import RestController, expose

class Root(RestController):

  @expose
  def post(self, request):
    '''
    @PUBLIC

    Create a new object.

    Parameters
    ----------

    i  : int
    n  : num
    s  : str
    b  : bool
      A boolean value.
    a  : any
    l  : list
    li : list(int)
      A list of integers.
    lm : list(null|bool|str|43)
    '''
