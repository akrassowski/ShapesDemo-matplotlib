#!/usr/bin/env python 

import unittest

from ConfigParser import ConfigParser
from parameterized import parameterized

class Testing(unittest.TestCase):

    def setUp(self):
        self.parser = ConfigParser(None)

    def test_normalize_xy_too_few(self):
        with self.assertRaises(ValueError):
            xy = self.parser.normalize_xy('too_few', (1, ))

    def test_normalize_xy_too_many(self):
        with self.assertRaises(ValueError):
            xy = self.parser.normalize_xy('too_many', (1, 2, 3))

class Test_normalize_shape(unittest.TestCase):
    def setUp(self):
        self.parser = ConfigParser(None)

    @parameterized.expand([
        ['Circle', 'C'],
        ['Square', 'S'],
        ['triangle', 'T'],
    ])
        
    def test_normalize_shape(self, param, result):
        shape = self.parser.normalize_shape(param)
        self.assertEqual(result, shape)

class Test_normalize_xy(unittest.TestCase):
    def setUp(self):
        self.parser = ConfigParser(None)

    @parameterized.expand([
        [(7.0, 9.0), (7,9)],
        [(7.1, 9.2), (7,9)]
    ])
        
    def test_normalize_xy(self, xy, result):
        xy = self.parser.normalize_xy('float', xy)
        self.assertEqual(result, xy)

if __name__ == '__main__':
    unittest.main()

