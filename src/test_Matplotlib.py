#!/usr/bin/env python
"""Tests for Matplotlib"""
import unittest
from unittest.mock import MagicMock
from Matplotlib import Matplotlib

# pylint: disable=missing-function-docstring, too-many-public-methods
class Test(unittest.TestCase):
    """Tests for Matplotlib"""

    @staticmethod
    def _minimal_args():
        args = MagicMock()
        args.graph_xy = (240, 270)
        args.figure_xy = (2, 3)
        args.position = 7
        return args

    def setUp(self):
        args = self._minimal_args()
        self.matplotlib = Matplotlib(args)

    def test_flip_0(self):
        value = self.matplotlib.flip_y(0)
        self.assertEqual(value, self.matplotlib.axes.get_ylim()[1])

    def test_flip_10(self):
        value = self.matplotlib.flip_y(10)
        self.assertEqual(value, 260)

    def test_ticks_on(self):
        args = self._minimal_args()
        args.ticks = True
        matplotlib = Matplotlib(args)
        self.assertTrue(matplotlib.axes.get_xaxis().get_visible())
        self.assertTrue(matplotlib.axes.get_yaxis().get_visible())

    def test_ticks_off(self):
        args = self._minimal_args()
        args.ticks = False
        matplotlib = Matplotlib(args)
        self.assertFalse(matplotlib.axes.get_xaxis().get_visible())
        self.assertFalse(matplotlib.axes.get_yaxis().get_visible())

if __name__ == '__main__':
    unittest.main()
    Test()
