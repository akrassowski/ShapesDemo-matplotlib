#!/usr/bin/env python

"""Testing of the ConnextSubscriber module"""
import unittest
from ConnextSubscriber import ConnextSubscriber
# pylint: disable=missing-function-docstring

class Test(unittest.TestCase):
    """Testing of the ConnextSubscriber module"""

    def setup(self):
        self.sub = ConnextSubscriber(args)

    def test_creat_default_sample(self):
        a = 'some'
        b = 'some'
        self.assertEqual(a, b)

    def test_boolean(self):
        a = True
        b = True
        self.assertEqual(a, b)

if __name__ == '__main__':
    unittest.main()
