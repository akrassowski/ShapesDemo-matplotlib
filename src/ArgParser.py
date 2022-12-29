#!/usr/bin/env python

###############################################################################
# (c) Copyright, Real-Time Innovations, 2021. All rights reserved.            #
# No duplications, whole or partial, manual or electronic, may be made        #
# without express written permission.  Any such copies, or revisions thereof, #
# must display this notice unaltered.                                         #
# This code contains trade secrets of Real-Time Innovations, Inc.             #
###############################################################################

"""Parse the arguments, apply sanity checks and return the args in a Namespace"""

# python imports
import argparse
import logging
# don't log here, since loglevel arg isn't set yet
# LOG = logging.getLogger(__name__)

# pylint: disable=too-few-public-methods
class BlankLinesHelpFormatter(argparse.HelpFormatter):
    """Respect multiple helplines"""
    def _split_lines(self, text, width):
        return text.splitlines()


class ArgParser:
    """helper class to parse command line arguments"""

    def __init__(self, default_dic):
        self.default_dic = default_dic

    def parse_args(self, vargs):
        """pass vargs to allow testing"""

        def validate_shape_letters(letters):
            """helper to check for valid abbreviations of shape name"""
            if len(letters) > 3:
                raise ValueError('Cannot subscribe to more then 3 Topics')
            for letter in letters:
                if letter.upper() not in "CST":
                    raise ValueError(f'Topic letters ({letter}) must be one or more of: ' +
                                     '"CST" for Circle, Square, Triangle')
            return letters.upper()

        def pair2str(pair):
            """show x,y as 'x y'"""
            return f'{pair[0]} {pair[1]}'

        default = self.default_dic
        parser = argparse.ArgumentParser(
            description="Simple ShapesDemo",
            formatter_class=BlankLinesHelpFormatter
        )
        parser.add_argument('--config', '-cfg', type=str,
                            help='filename of JSON cfg file [None]')
        parser.add_argument('--config_help', '-ch', action='store_true',
                            help='print pub and sub config dictionaries and exit')
        parser.add_argument('--domain_id', '-d', type=int, default=default['DOMAIN_ID'],
                            help="Specify Domain number 0-122 [default['DOMAIN_ID']")
        parser.add_argument('--extended', action=argparse.BooleanOptionalAction,
                            help='Use ShapeTypeExtended for all shapes [ShapeType]')
        parser.add_argument('-f', '--figure_xy', default=(default['FIG_XY']),
                            nargs=2, metavar=('x', 'y'), type=float,
                            help=("width and height of figure in inches as two floats " +
                                  f"[{pair2str(default['FIG_XY'])}]"))
        parser.add_argument('-g', '--graph_xy', default=(default['MAX_XY']),
                            nargs=2, metavar=('x', 'y'), type=int,
                            help=("width and height of graph in pixels as two integers" +
                                  f"[{pair2str(default['MAX_XY'])}]"))
        parser.add_argument('-i', '--index', type=int, default=None,
                            help=('screen slot index as 2 rows of 5 [1]-10\n' +
                                  'For absolute x,y positioning use --position'))
        parser.add_argument('--log_level', '-l', type=int, default=logging.INFO,
                            help="logger level [40=INFO]")
        parser.add_argument('--position', '-p', default=None, nargs=2, metavar=('x' 'y'), type=int,
                            help=('screen position in pixels as two integers\n' +
                                  'For simpler slot placement, use --index'))
        parser.add_argument('--qos_file', '-qf', type=str, default=default['QOS_FILE'],
                            help=f"full path of QoS file [{default['QOS_FILE']}]")
        parser.add_argument('--qos_lib', '-ql', type=str, default=default['QOS_LIB'],
                            help=f"QoS library name [{default['QOS_LIB']}]")
        parser.add_argument('--qos_profile', '-qp', type=str, default=default['QOS_PROFILE'],
                            help=f"QoS profile name [{default['QOS_PROFILE']}]")
        parser.add_argument('--subtitle', '-st', type=str, default="",
                            help='Provide a subtitle to the widget [""]')
        parser.add_argument('--title', '-t', type=str, default=default['TITLE'],
                            help=f"Provide a title to the widget [{default['TITLE']}]")
        parser.add_argument('--ticks', action=argparse.BooleanOptionalAction,
                            help='Show tick marks on axes [False]')

        parser.add_argument('--subscribe', '-sub', type=validate_shape_letters, default="S",
                            help='simple subscriber to any of Circle, Square, Triangle [S]')

        parser.add_argument('--publish', '-pub', type=validate_shape_letters,  ## default="S"
                            help=('simple publisher of Circle, Square, Triangle ' +
                                  '[no default, must select]'))

        # internal args used whilst developing/debugging only
        parser.add_argument('--justdds', '-j', type=int,
                            help='just call dds draw this many times, no graphing, for testing')
        parser.add_argument('--nap', '-n', type=float, default=0,
                            help='intrasample naptime [default:0.0]')

        args = parser.parse_args(vargs)

        # for now, priortize sub over pub
        if args.publish:  # since pub has no default, any setting trumps subscribe
            args.subscribe = None
        else:  # otherwise, assume sub
            args.publish = None

        if args.position is None:
            if args.index is None:
                args.position = 1
            else:
                args.position = args.index

        return args
