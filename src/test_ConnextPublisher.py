#!/usr/bin/env python
"""Test ConnextPublisher"""
import logging
import unittest
from unittest.mock import MagicMock #, patch
from ArgParser import ArgParser
from ConfigParser import ConfigParser
from ConnextPublisher import ConnextPublisher
from ShapesDemo import DEFAULT_DIC

LOG = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s %(filename)s-%(funcName)s:%(lineno)d %(message)s'
)
# pylint: disable=missing-function-docstring

class Test(unittest.TestCase):
    """Test ConnextPublisher"""

    def setUp(self):
        arg_parser = ArgParser(DEFAULT_DIC)
        args = arg_parser.parse_args(["-d", "27", "-pub", "S", "--nap", "2000"])
        print(f'{args=}')
        config_parser = ConfigParser(DEFAULT_DIC)
        parsed_args, is_pub, self.config = config_parser.get_config(args)
        LOG.info(f'setUp called {self.config=}')
        self.assertTrue(is_pub)
        self.pub = ConnextPublisher(MagicMock(), parsed_args, self.config)

    def test_create_default_sample(self):
        sample = self.pub.create_default_sample(self.config[0])
        self.assertEqual(sample.color, 'BLUE')

    #@patch('time.sleep', return_value=None)
    def test_sleep_as_needed(self):
        self.pub.sleep_as_needed()
        #self.assertEqual(1, patched_time_sleep.call_count)



if __name__ == '__main__':
    unittest.main()
    Test()
