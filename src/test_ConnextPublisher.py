#!/usr/bin/env python 

import unittest
from ArgParser import ArgParser
from ConnextPublisher import ConnextPublisher

class Testing(unittest.TestCase):

    def setUp(self):
        s = ArgParser()
        args = ArgParser().parse_args("", "TESTPublisher")
        self.pub = ConnextPublisher(args)

    def test_create_default_sample(self):
        sample = self.pub.create_default_sample('S')
        self.assertEqual(sample.color, 'BLUE')

    def test_create_default_sample2(self):
        sample = self.pub.create_default_sample2('S')
        self.assertEqual(sample.color, 'BLUE')


if __name__ == '__main__':
    unittest.main()

