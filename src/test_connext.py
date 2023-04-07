#!/usr/bin/env python
"""Test ConnextPublisher"""
import logging
import unittest
from unittest.mock import MagicMock #, patch
from arg_parser import ArgParser
from config_parser import ConfigParser
from connext import Connext
from shapes_demo import DEFAULT_DIC

LOG = logging.getLogger(__name__)
logging.basicConfig(
    # level=logging.INFO,
    level=logging.CRITICAL,
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
        self.connext = Connext(MagicMock(), parsed_args)

    def test_get_center_square(self):
        square_points = [[141, 33], [141, 63], [171, 63], [171, 33], [141, 33]]
        center_x, center_y = self.connext._get_center(square_points)
        self.assertEqual(center_x, 156)
        self.assertEqual(center_y, 48)

    # pylint: disable=protected-access
    def test_get_center_triangle(self):
        triangle_points = [[128, 265], [143, 235], [113, 235], [128, 265]]
        center_x, center_y = self.connext._get_center(triangle_points)
        self.assertEqual(center_x, 128)
        self.assertEqual(center_y, 250)

    def test_get_center_circle(self):
        circle_points = [[141, 33], [141, 63], [171, 63], [171, 33], [141, 33]]
        center_x, center_y = self.connext._get_center(circle_points)
        self.assertEqual(center_x, 156)
        self.assertEqual(center_y, 48)

if __name__ == '__main__':
    unittest.main()
    Test()
