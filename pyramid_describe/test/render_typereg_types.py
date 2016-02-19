from pyramid_controllers import RestController, expose

class Root(RestController):

  @expose
  def post(self, request):
    '''
    @PUBLIC

    Create a new shape.

    Parameters
    ----------

    shape : Shape

      The new shape to create.

      @PUBLIC

      A `Shape` is a polygon with three or more sides.

      sides : int

        The number of sides this shape has.

    Returns
    -------

    shape : Shape

    '''

  @expose
  def get(self, request):
    '''
    @PUBLIC

    Get a list of all currently registered shapes.

    Returns
    -------

    shapes : Shape

      @PUBLIC

      A `Shape` is a polygon with three or more sides.

      sides : int

        The number of sides this shape has.

      created : num

        The epoch timestamp that this shape was created.
    '''

    ## TODO: change this to:
    ##   shapes : list(Shape)
    ## when supported.

  @expose
  def favorite(self, request):
    '''
    @PUBLIC

    Returns
    -------

    shape : Triangle

      @PUBLIC

      A `Triangle` is a `Shape` with three sides.
      sides : 3
      equilateral : bool, default: true
        Whether or not the sides of this triangle
        are the same length.
      examples : dict
        Just some examples of using parameter examples.
        str : str, example: 'foo', example: 'bar'
        stuff : any, examples: null|32 |-0.57 |'foo'|false
    '''
