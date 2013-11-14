# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2013/11/14
# copy: (C) Copyright 2013 Cadit Health Inc., All Rights Reserved.
#------------------------------------------------------------------------------

from docutils.core import publish_cmdline, default_description

from . import rst

description = \
  'Converts reStructuredText source(s) into a single, canonical' \
  ' reStructuredText document. ' + default_description

def main(args=None):
  publish_cmdline(writer=rst.Writer(), description=description)

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
