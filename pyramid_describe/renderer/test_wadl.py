# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2016/01/03
# copy: (C) Copyright 2016-EOT Cadit Inc., All Rights Reserved.
#------------------------------------------------------------------------------

from __future__ import absolute_import

import re
import unittest
import xml.etree.ElementTree as ET

import pxml
from pyramid_controllers.test_helpers import TestHelper

from pyramid_describe.controller import DescribeController
from ..test_describe import SimpleRoot

#------------------------------------------------------------------------------
# make the XML namespace output a bit easier to grok...
ET.register_namespace('wadl', 'http://wadl.dev.java.net/2009/02')
ET.register_namespace('xsd',  'http://www.w3.org/2001/XMLSchema')
ET.register_namespace('xsi',  'http://www.w3.org/2001/XMLSchema-instance')
ET.register_namespace('doc',  'http://pythonhosted.org/pyramid_describer/xmlns/0.1/doc')
ET.register_namespace('app',  'http://localhost')

#------------------------------------------------------------------------------
class TestWadl(TestHelper, pxml.XmlTestMixin):

  #----------------------------------------------------------------------------
  def test_format_wadl(self):
    ## The Describer can render WADL
    root = SimpleRoot()
    root.desc = DescribeController(
       root, doc='URL tree description.',
       settings={
        'format.default': 'wadl',
        'index-redirect': 'false',
        'entry.parsers': 'pyramid_describe.test_describe.docsEnhancer',
        'exclude': '|^/desc/.*|',
       })
    res = self.send(root, '/desc')

    # TODO: create a unit test for dynamically created paths... eg.
    #       transform "/api/book/{BOOK_ID}" to
    #         <resource "api/book">
    #           <resource "{BOOK_ID}">
    #             <param name="BOOK_ID" style="template" type="xsd:string"/>
    #             ...
    #           </resource>
    #         </resource>

    chk = '''
<application
 xmlns="http://wadl.dev.java.net/2009/02"
 xmlns:xsd="http://www.w3.org/2001/XMLSchema"
 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
 xmlns:doc="http://pythonhosted.org/pyramid_describer/xmlns/0.1/doc"
 xmlns:app="http://localhost"
 xsi:schemaLocation="http://wadl.dev.java.net/2009/02 wadl.xsd"
 >

 <grammars>

  <xsd:schema
   targetNamespace="http://localhost"
   app:targetNamespace="http://localhost"
   elementFormDefault="qualified"
   >
   <xsd:complexType name="HTTPForbidden">
    <xsd:element name="code" minOccurs="1" maxOccurs="1">
     <xsd:simpleType>
      <xsd:restriction base="xsd:integer">
       <xsd:enumeration value="403"/>
      </xsd:restriction>
     </xsd:simpleType>
    </xsd:element>
    <xsd:element maxOccurs="1" minOccurs="1" name="message">
     <xsd:simpleType>
      <xsd:restriction base="xsd:string">
       <xsd:enumeration value="Forbidden" />
      </xsd:restriction>
     </xsd:simpleType>
    </xsd:element>
    <doc:doc>Access was denied to this resource.</doc:doc>
   </xsd:complexType>
   <xsd:complexType name="HTTPUnauthorized">
    <xsd:element name="code" minOccurs="1" maxOccurs="1">
     <xsd:simpleType>
      <xsd:restriction base="xsd:integer">
       <xsd:enumeration value="401"/>
      </xsd:restriction>
     </xsd:simpleType>
    </xsd:element>
    <xsd:element maxOccurs="1" minOccurs="1" name="message">
     <xsd:simpleType>
      <xsd:restriction base="xsd:string">
       <xsd:enumeration value="Unauthorized" />
      </xsd:restriction>
     </xsd:simpleType>
    </xsd:element>
    <doc:doc>This server could not verify that you are authorized to access the document you requested.  Either you supplied the wrong credentials (e.g., bad password), or your browser does not understand how to supply the credentials required.</doc:doc>
   </xsd:complexType>
  </xsd:schema>

 </grammars>

 <resources base="http://localhost">
  <resource path="">
   <doc:doc>The default root.</doc:doc>
   <method name="GET"/>
  </resource>
  <resource path="desc">
   <doc:doc>URL tree description.</doc:doc>
   <method name="GET"/>
  </resource>
  <resource path="rest">
   <doc:doc>A RESTful entry.</doc:doc>
   <method name="POST">
    <doc:doc>Creates a new entry.</doc:doc>

    <request>
     <representation>
      <xsd:complexType>
       <xsd:element name="size" maxOccurs="1" minOccurs="0">
        <doc:doc>The anticipated maximum size</doc:doc>
        <xsd:simpleType>
         <xsd:restriction base="xsd:integer"/>
        </xsd:simpleType>
       </xsd:element>
       <xsd:element name="text" maxOccurs="1" minOccurs="1">
        <doc:doc>The text content for the posting</doc:doc>
        <xsd:simpleType>
         <xsd:restriction base="xsd:string"/>
        </xsd:simpleType>
       </xsd:element>
      </xsd:complexType>
     </representation>
    </request>

    <response status="200">
     <representation>
      <xsd:element ref="xsd:string">
       <doc:doc>The ID of the new posting</doc:doc>
      </xsd:element>
     </representation>
    </response>

    <response status="401">
     <representation>
      <xsd:element ref="app:HTTPUnauthorized">
       <doc:doc>Authenticated access is required</doc:doc>
      </xsd:element>
     </representation>
    </response>

    <response status="403">
     <representation>
      <xsd:element ref="app:HTTPForbidden">
       <doc:doc>The user does not have posting privileges</doc:doc>
      </xsd:element>
     </representation>
    </response>

   </method>
   <method name="GET">
    <doc:doc>Gets the current value.</doc:doc>
   </method>
   <method name="PUT">
    <doc:doc>Updates the value.</doc:doc>
   </method>
   <method name="DELETE">
    <doc:doc>Deletes the entry.</doc:doc>
   </method>
  </resource>
  <resource path="sub/method">
   <doc:doc>This method outputs a JSON list.</doc:doc>
   <method name="GET"/>
  </resource>
  <resource path="swi">
   <doc:doc>A sub-controller providing only an index.</doc:doc>
   <method name="GET"/>
  </resource>
  <resource path="unknown">
   <doc:doc>A dynamically generated sub-controller.</doc:doc>
   <method name="GET"/>
  </resource>
 </resources>

</application>
'''

    # todo: what to do about mediaType, status, and namespaces?...
    # <representation mediaType="application/xml" element="yn:ResultSet"/>
    # <fault status="400" mediaType="application/xml" element="ya:Error"/>
    def roundtrip(xml):
      return ET.tostring(ET.fromstring(xml), 'UTF-8')

    chk = ET.tostring(ET.fromstring(re.sub('>\s*<', '><', chk, flags=re.MULTILINE)), 'UTF-8')
    res.body = roundtrip(res.body)
    self.assertResponse(res, 200, chk, xml=True)

#------------------------------------------------------------------------------
# end of $Id$
# $ChangeLog$
#------------------------------------------------------------------------------
