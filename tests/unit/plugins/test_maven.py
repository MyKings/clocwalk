#!/usr/bin/env python
# coding: utf-8

import os

from tests.common import TestCase
from tests.common import EXAMPLE_DATA_PATH
from xml.etree import ElementTree

from clocwalk.plugins.maven import start


class POMTestCase(TestCase):

    def setUp(self):
        self.pom_dir = [
            'a/a1/pom.xml',
            'b/pom.xml',
            'c/c1/pom.xml',
            'c/c2/pom.xml',
            'pom.xml',
        ]

    def test_start_include_dir(self):
        result = start(code_dir=os.path.join(EXAMPLE_DATA_PATH, 'plugins', 'pom', 'c'), skipNewVerCheck=True)
        for item in result:
            self.assertTrue(item)

    def test_start_3_dir(self):
        result = start(code_dir=os.path.join(EXAMPLE_DATA_PATH, 'plugins', 'pom'), skipNewVerCheck=True)
        for item in result:
            self.assertIn(item['origin'], self.pom_dir)

    def test_start_new_version(self):
        result = start(code_dir=os.path.join(EXAMPLE_DATA_PATH, 'plugins', 'pom', 'a'))
        for item in result:
            self.assertIsNotNone(item['new_version'])

    def test_start_dir(self):
        result = start(code_dir='', skipNewVerCheck=True, tag_filter=['org.mybatis.generator'])
        for item in result:
            self.assertIn(item['origin'], self.pom_dir)
