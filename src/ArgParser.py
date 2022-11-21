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

LOG = logging.getLogger(__name__)

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
                    raise ValueError('Topic letters ({letter}) must be one or more of: ' +
                                     '"CST" for Circle, Square, Triangle')
            return letters.upper()

        default = self.default_dic
        parser = argparse.ArgumentParser(
            description="Simple ShapesDemo")
        parser.add_argument('--config', '-cfg', type=str,
                            help='filename of JSON cfg file [None]')
        parser.add_argument('--config_help', '-ch', action='store_true',
                            help='print pub and sub config dictionaries and exit')
        parser.add_argument('--domain_id', '-d', type=int, default=default['DOMAIN_ID'],
                            help="Specify Domain number 0-122 [default['DOMAIN_ID']")
        parser.add_argument('--extended', action=argparse.BooleanOptionalAction,
                            help='Use ShapeTypeExtended [ShapeType]')
        parser.add_argument('-f', '--figure_xy', default=default['FIG_XY'], type=int,
                            help=f"x,y of figure in inches [{default['FIG_XY']}]")
        parser.add_argument('-g', '--graph_xy', default=(default['MAX_XY']), type=int,
                            help=f"width and height of graph in pixels [{default['MAX_XY']}]")
        parser.add_argument('-i', '--index', type=int, default=1,
                            help='screen slot index [1]-6')
        parser.add_argument('--log_level', '-l', type=int, default=logging.INFO,
                            help="logger level [40=INFO]")
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

        parser.add_argument('--subscribe', '-sub', type=validate_shape_letters, default="S",
                            help='simple subscriber to any of Circle, Square, Triangle [S]')

        parser.add_argument('--publish', '-pub', type=validate_shape_letters,  ## default="S"
                            help='simple publisher of Circle, Square, Triangle [no default, must select]')

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

        LOG.info(f'{args=}')
        return args
