#!/usr/bin/env python 

import unittest
from ConnextSubscriber import ConnextSubscriber

class Testing(unittest.TestCase):

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

