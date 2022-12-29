#!/usr/bin/env python

"""Testing of the ConnextSubscriber module"""
import unittest
from unittest.mock import MagicMock

from ConnextSubscriber import ConnextSubscriber
# pylint: disable=missing-function-docstring

class Test(unittest.TestCase):
    """Testing of the ConnextSubscriber module"""

    def setUp(self):
        self.sub = ConnextSubscriber(MagicMock(), MagicMock(), MagicMock())

    def silly(self):
        self.assertIsNotNone(self.sub)

if __name__ == '__main__':
    unittest.main()
    Test()
