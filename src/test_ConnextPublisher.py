#!/usr/bin/env python 

import logging
import unittest
from ArgParser import ArgParser
from ConfigParser import ConfigParser
from ConnextPublisher import ConnextPublisher
from ShapesDemo import DEFAULT_DIC

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
#LOG.setLevel(logging.DEBUG)

class Test(unittest.TestCase):

    def setUp(self):
        parser = ArgParser(DEFAULT_DIC)
        args = parser.parse_args(["-d", "27", "-pub", "S"])
        parser = ConfigParser(DEFAULT_DIC)
        parsed_args, is_pub, config = parser.get_config(args) 
        self.assertTrue(is_pub)
        self.pub = ConnextPublisher(parsed_args, config)

    def test_create_default_sample(self):
        sample = self.pub.create_default_sample('S')
        self.assertEqual(sample.color, 'BLUE')

if __name__ == '__main__':
    unittest.main()

