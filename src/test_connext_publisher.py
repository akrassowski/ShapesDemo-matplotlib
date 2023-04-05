#!/usr/bin/env python
"""Test ConnextPublisher"""
import logging
import unittest
from unittest.mock import MagicMock #, patch
from arg_parser import ArgParser
from config_parser import ConfigParser
from connext_publisher import ConnextPublisher
from shapes_demo import DEFAULT_DIC

LOG = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.WARN,
    format='%(levelname)s %(filename)s-%(funcName)s:%(lineno)d %(message)s'
)
# pylint: disable=missing-function-docstring

class Test(unittest.TestCase):
    """Test ConnextPublisher"""

    def setUp(self):
        arg_parser = ArgParser(DEFAULT_DIC)
        args = arg_parser.parse_args(["-d", "27", "-pub", "S"])
        LOG.info(f'{args=}')
        config_parser = ConfigParser(DEFAULT_DIC)
        parsed_args, is_pub, self.config = config_parser.get_config(args)
        LOG.info(f'setUp called {self.config=}')
        self.assertTrue(is_pub)
        self.pub = ConnextPublisher(MagicMock(), parsed_args, self.config)

    def test_create_default_sample(self):
        sample = self.pub.create_default_sample(self.config[0])
        self.assertEqual(sample.color, 'BLUE')

if __name__ == '__main__':
    unittest.main()
    Test()
