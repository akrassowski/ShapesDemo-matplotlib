#!/usr/bin/env python

###############################################################################
# (c) Copyright, Real-Time Innovations, 2021. All rights reserved.            #
# No duplications, whole or partial, manual or electronic, may be made        #
# without express written permission.  Any such copies, or revisions thereof, #
# must display this notice unaltered.                                         #
# This code contains trade secrets of Real-Time Innovations, Inc.             #
###############################################################################

"""Subscribes or Publishes Shapes and displays them"""

# python imports
import argparse
import logging

LOG = logging.getLogger(__name__)

class ArgParser:
    """trivial class scope for the arg parser"""
    MAXX, MAXY = 240, 270

    def parse_args(self, args, _default_title="Title"):
        """pass args to allow testing"""
        FIGX, FIGY = 2.375, 2.72  # match RTI ShapesDemo box size
        DEFAULT_QOS_FILE = './SimpleShape.xml'
        DEFAULT_QOS_LIB, DEFAULT_QOS_PROFILE = 'MyQosLibrary', 'MyProfile'
        DEFAULT_HISTORY_DEPTH = 6

        def validate_shape_letters(letters):
            if len(letters) > 3:
                raise ValueError('Cannot subscribe to more then 3 Topics')
            for letter in letters:
                if letter.upper() not in "CST":
                    raise ValueError('Topic letters ({letter}) must be one or more of: ' +
                                     '"CST" for Circle, Square, Triangle')
            return letters.upper()

        parser = argparse.ArgumentParser(
            description="Simple ShapesDemo")
        parser.add_argument('--config', '-cfg', type=str,
                            help=f'filename of JSON cfg file [None]')
        parser.add_argument('--config_help', '-ch', action='store_true',
                            help=f'print pub and sub config dictionaries and exit')
        parser.add_argument('--domain_id', '-d', type=int, default=0,
                            help='Specify Domain on which to listen [0]-122')
        parser.add_argument('--extended', action=argparse.BooleanOptionalAction,
                            help='Use ShapeTypeExtended [ShapeType]')
        parser.add_argument('-f', '--figureXY', default=(FIGX, FIGY), type=int, nargs=2,
                            help=f'x,y of figure in inches [{FIGX},{FIGY}]')
        parser.add_argument('-g', '--graphXY', default=(self.MAXX, self.MAXY), type=int, nargs=2,
                            help=f'width and height of graph in pixels [{self.MAXX},{self.MAXY}]')
        parser.add_argument('-i', '--index', type=int, default=1,
                            help=f'screen slot index [1]-6')
        parser.add_argument('--log_level', '-l', type=int, default=logging.INFO,
                            help="logger level [40=INFO]")
        parser.add_argument('--qos_file', '-qf', type=str, default=DEFAULT_QOS_FILE,
                            help=f'full path of QoS file [{DEFAULT_QOS_FILE}]')
        parser.add_argument('--qos_lib', '-ql', type=str, default=DEFAULT_QOS_LIB,
                            help=f'QoS library name [{DEFAULT_QOS_LIB}]')
        parser.add_argument('--qos_profile', '-qp', type=str, default=DEFAULT_QOS_PROFILE,
                            help=f'QoS profile name [{DEFAULT_QOS_PROFILE}]')
        parser.add_argument('--subtitle', '-st', type=str, default="",
                            help=f'Provide a subtitle to the widget [""]')
        parser.add_argument('--title', '-t', type=str, default=_default_title,
                            help=f'Provide a title to the widget [{_default_title}]')

        parser.add_argument('--subscribe', '-sub', type=validate_shape_letters, default="S",
                            help=f'simple subscriber to any of Circle, Square, Triangle [S]')

        ### these args will override XML QoS
        parser.add_argument('--history_depth', '-hd', type=int,
                            help=f'XML Override: history depth for all topics [{DEFAULT_HISTORY_DEPTH}]')

        parser.add_argument('--publish', '-pub', type=validate_shape_letters,
                            help=f'simple publisher of any of Circle, Square, Triangle [S]')

        # internal args used whilst developing/debugging only
        parser.add_argument('--justdds', '-j', type=int,
                            help='just call dds draw this many times, no graphing, for testing')
        parser.add_argument('--nap', '-n', type=float, default=0,
                            help=f'intrasample naptime [default:0.0]')

        args = parser.parse_args()
        args.graphx, args.graphy = args.graphXY
        if args.publish:
            args.subscribe = None
        LOG.debug(f'{args=}')
        return args

