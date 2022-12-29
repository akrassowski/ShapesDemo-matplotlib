#!/usr/bin/env python
"""Tests for Matplotlib"""
import unittest
from unittest.mock import MagicMock
from Matplotlib import Matplotlib

# pylint: disable=missing-function-docstring, too-many-public-methods
class Test(unittest.TestCase):
    """Tests for Matplotlib"""

    def setUp(self):
        args = MagicMock()
        args.graph_xy = (240, 270)
        args.figure_xy = (2, 3)
        self.matplotlib = Matplotlib(args)

    def test_flip_0(self):
        value = self.matplotlib.flip_y(0)
        self.assertEqual(value, self.matplotlib.axes.get_ylim()[1])

    def test_flip_10(self):
        value = self.matplotlib.flip_y(10)
        self.assertEqual(value, 260)

if __name__ == '__main__':
    unittest.main()
    Test()
