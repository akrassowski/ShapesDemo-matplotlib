#!/usr/bin/env python
"""tests for ArgParser"""

import unittest
#import logging

from ArgParser import ArgParser
from ShapesDemo import DEFAULT_DIC

#LOG = logging.getLogger(__name__)
#logging.basicConfig(level=logging.DEBUG)

# pylint: disable=missing-function-docstring
class Test(unittest.TestCase):
    """tests for ConnextSubscriber"""
    def setUp(self):
        self.parser = ArgParser(DEFAULT_DIC)

    def test_defaults(self):
        args = self.parser.parse_args([])
        #print(args)
        self.assertEqual(args.figure_xy, DEFAULT_DIC['FIG_XY'])
        self.assertEqual(args.graph_xy, DEFAULT_DIC['MAX_XY'])
        self.assertEqual(args.domain_id, DEFAULT_DIC['DOMAIN_ID'])
        self.assertEqual(args.qos_file, DEFAULT_DIC['QOS_FILE'])
        self.assertEqual(args.qos_lib, DEFAULT_DIC['QOS_LIB'])
        self.assertEqual(args.qos_profile, DEFAULT_DIC['QOS_PROFILE'])
        # not cmd-line option self.assertEqual(args.color, DEFAULT_DIC['COLOR'])
        self.assertEqual(args.title, DEFAULT_DIC['TITLE'])

    def test_implicit_defaults(self):
        args = self.parser.parse_args([])
        self.assertEqual(args.index, None)
        self.assertEqual(args.position, 1)
        self.assertEqual(bool(args.extended), False)
        self.assertEqual(args.subscribe, 'S')
        self.assertEqual(args.publish, None)
        self.assertEqual(args.nap, 0)

    def test_publish_triangle(self):
        cmdline = ['--publish', 't']
        args = self.parser.parse_args(cmdline)
        self.assertEqual(bool(args.subscribe), False)
        self.assertEqual(args.publish, 'T')

    def test_invalid_shape(self):
        cmdlines = [ ['--subscribe', 'a'], ['--publish', 'z'] ]
        for cmdline in cmdlines:
            #(ArgumentError): - false failure since ValueError is raised and caught by argparse lib
            with self.assertRaises(BaseException):  # must catch both ValueError and SysExit
                _ = self.parser.parse_args(cmdline)

    def test_figure_and_graph(self):
        cmdline = ['--figure_xy', '1', '2', '--graph_xy', '3', '4']
        args = self.parser.parse_args(cmdline)
        self.assertEqual(args.figure_xy[0], 1)
        self.assertEqual(args.figure_xy[1], 2)
        self.assertEqual(args.graph_xy[0], 3.0)
        self.assertEqual(args.graph_xy[1], 4.0)

if __name__ == '__main__':
    unittest.main()
    Test()  # keep pylint happy
