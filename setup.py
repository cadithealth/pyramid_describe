#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2013/09/09
# copy: (C) Copyright 2013 Cadit Health Inc., All Rights Reserved.
#------------------------------------------------------------------------------

import os, sys, setuptools
from setuptools import setup, find_packages

# require python 2.7+
if sys.hexversion < 0x02070000:
  raise RuntimeError('This package requires python 2.7 or better')

heredir = os.path.abspath(os.path.dirname(__file__))
def read(*parts):
  try:    return open(os.path.join(heredir, *parts)).read()
  except: return ''

test_dependencies = [
  'nose                 >= 1.3.0',
  'coverage             >= 3.6',
  ]

dependencies = [
  'distribute           >= 0.6.24',
  'iniherit             >= 0.1.6',
  'pyramid              >= 1.4.2',
  ]

entrypoints = {
  'console_scripts': [
    'pinspect           = pyramid_inspect.cli:main',
    ],
  }

classifiers = [
  'Development Status :: 1 - Planning',
  #'Development Status :: 2 - Pre-Alpha',
  #'Development Status :: 3 - Alpha',
  #'Development Status :: 4 - Beta',
  #'Development Status :: 5 - Production/Stable',
  'Intended Audience :: Developers',
  'Programming Language :: Python',
  'Operating System :: OS Independent',
  'Natural Language :: English',
  'License :: OSI Approved :: MIT License',
  'License :: Public Domain',
  ]

setup(
  name                  = 'pyramid_inspect',
  version               = '0.0.1',
  description           = 'A pyramid plugin that inspects and renders a pyramid application URL hierarchy.',
  long_description      = read('README.rst'),
  classifiers           = classifiers,
  author                = 'Philip J Grabner, Cadit Health Inc',
  author_email          = 'oss@cadit.com',
  url                   = 'http://github.com/cadithealth/pyramid_inspect',
  keywords              = 'pyramid application url inspection reflection',
  packages              = find_packages(),
  platforms             = ['any'],
  include_package_data  = True,
  zip_safe              = True,
  install_requires      = dependencies,
  tests_require         = test_dependencies,
  test_suite            = 'pyramid_inspect',
  entry_points          = entrypoints,
  license               = 'MIT (http://opensource.org/licenses/MIT)',
  )

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
