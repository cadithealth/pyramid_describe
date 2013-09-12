# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2013/09/09
# copy: (C) Copyright 2013 Cadit Health Inc., All Rights Reserved.
#------------------------------------------------------------------------------

import logging
from wsgiref.simple_server import make_server
from pyramid.config import Configurator
from pyramid.response import Response
from pyramid_controllers import \
  Controller, RestController, \
  expose, index, lookup

class ContactController(RestController):
  'RESTful access to a specific contact.'
  @expose
  def get(self, request):
    'Get this contact\'s details.'
    return 'ok.get:' + request.cid
  @expose
  def put(self, request):
    'Update this contact\'s details.'
    return 'ok.put:' + request.cid
  @expose
  def delete(self, request):
    'Delete this contact.'
    return 'ok.delete:' + request.cid

class ContactDispatcher(RestController):
  'Contact manager.'
  @expose
  def post(self, request):
    'Creates a new \'contact\' object.'
    return 'ok.post'
  CONTACTID = ContactController(expose=False)
  @lookup
  def lookup(self, request, contact_id, *rem):
    request.cid = contact_id
    return (self.CONTACTID, rem)

class RootController(Controller):
  contact = ContactDispatcher()
  @index
  def index(self, request):
    'The application root.'
    return 'ok.index'
  @expose
  def login(self, request):
    'Authenticate against the server.'
    return 'ok.login'
  @expose
  def logout(self, request):
    'Remove authentication tokens.'
    return 'ok.logout'

def main(global_config, **settings):
  config = Configurator()
  config.include('pyramid_controllers')
  # TODO: add support for non-controller views...
  # config.add_route('hello', '/hello/{name}')
  # config.add_view(hello_world, route_name='hello')
  # TODO: add support for static views...
  config.add_static_view('static', 'test_data/static')
  config.add_controller('root', '/', RootController())
  return config.make_wsgi_app()

if __name__ == '__main__':
  logging.basicConfig()
  app = main({})
  server = make_server('0.0.0.0', 8080, app)
  server.serve_forever()

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
