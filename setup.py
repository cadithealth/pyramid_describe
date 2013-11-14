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
def read(*parts, **kw):
  try:    return open(os.path.join(heredir, *parts)).read()
  except: return kw.get('default', '')

test_dependencies = [
  'nose                 >= 1.3.0',
  'coverage             >= 3.6',
  'WebTest              >= 1.4.0',
  'PyYAML               >= 3.10',
  'pdfkit               >= 0.4.1',
  ]

dependencies = [
  'distribute           >= 0.6.24',
  'argparse             >= 1.2.1',
  'pyramid              >= 1.4.2',
  'pyramid-controllers  >= 0.3.18',
  'pyramid-iniherit     >= 0.1.7',
  'six                  >= 1.4.1',
  'docutils             >= 0.10',
  ]

extras_dependencies = {
  'yaml': 'PyYAML       >= 3.10',
  'pdf':  'pdfkit       >= 0.4.1',
  }

entrypoints = {
  'console_scripts': [
    'pdescribe          = pyramid_describe.cli:main',
    'rst2rst.py         = pyramid_describe.writers.tools_rst2rst:main',
    ],
  }

classifiers = [
  'Development Status :: 4 - Beta',
  #'Development Status :: 5 - Production/Stable',
  'Intended Audience :: Developers',
  'Programming Language :: Python',
  'Operating System :: OS Independent',
  'Natural Language :: English',
  'License :: OSI Approved :: MIT License',
  'License :: Public Domain',
  ]

setup(
  name                  = 'pyramid_describe',
  version               = read('VERSION.txt', default='0.0.1').strip(),
  description           = 'A pyramid plugin that describes a pyramid application URL hierarchy via inspection.',
  long_description      = read('README.rst'),
  classifiers           = classifiers,
  author                = 'Philip J Grabner, Cadit Health Inc',
  author_email          = 'oss@cadit.com',
  url                   = 'http://github.com/cadithealth/pyramid_describe',
  keywords              = 'pyramid application url inspection reflection description describe',
  packages              = find_packages(),
  platforms             = ['any'],
  include_package_data  = True,
  zip_safe              = True,
  install_requires      = dependencies,
  extras_require        = extras_dependencies,
  tests_require         = test_dependencies,
  test_suite            = 'pyramid_describe',
  entry_points          = entrypoints,
  license               = 'MIT (http://opensource.org/licenses/MIT)',
  )

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
