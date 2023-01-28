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
import textwrap
# don't log here, since loglevel arg isn't set yet
# LOG = logging.getLogger(__name__)

# pylint: disable=too-few-public-methods
class BlankLinesHelpFormatter(argparse.RawDescriptionHelpFormatter):
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

        description = textwrap.dedent("""
            %(prog)s - Alternate Shapes Demo using Connext Python API 
            Some simple examples: 
                
                %(prog)s --publish S   # Minimal Blue Square publisher
                
                %(prog)s --subscribe CST   # Minimal subscriber to Circle, Square and Triangle topics

            Other behaviors can be specified in the QoS file.
            More options can be specified via the --config flag; see --config_help for help with the JSON format of .cfg files
        """
        )
        epilog = textwrap.dedent("""
            Coordinates system has bottom-left=0,0 increasing to the right and up.
            Values are published with the Y-axis values "flipped" so that the Java Shapes Demo can plot them correctly.
            Subscribers expect Java Shapes Demo values (where Y-axis is inverted). 
        """)

        parser = argparse.ArgumentParser(
            description=description,
            formatter_class=BlankLinesHelpFormatter,
            epilog=epilog
        )
        parser.add_argument('--config', '-cfg', type=str,
            help='Specify the filename of a JSON cfg file [None]')
        parser.add_argument('--config_help', '-ch', action='store_true',
            help='Print the publish and subscribe config dictionaries and exit')
        parser.add_argument('--domain_id', '-d', type=int, default=self.default_dic['DOMAIN_ID'],
            help="Specify Domain number 0-122 [default['DOMAIN_ID']")
        parser.add_argument('--extended', action=argparse.BooleanOptionalAction,
            help='Use ShapeTypeExtended for all shapes [ShapeType]')
        parser.add_argument('-f', '--figure_xy', default=(self.default_dic['FIG_XY']),
            nargs=2, metavar=('x', 'y'), type=float,
            help=("Specify the width and height of the figure in inches as two floats " +
                  f"[{pair2str(self.default_dic['FIG_XY'])}]"))
        parser.add_argument('-g', '--graph_xy', default=(self.default_dic['MAX_XY']),
            nargs=2, metavar=('x', 'y'), type=int,
            help=("Specify the width and height of the graph in pixels as two integers" +
                  f"[{pair2str(self.default_dic['MAX_XY'])}]"))
        parser.add_argument('-i', '--index', type=int, default=None,
            help=('Specify the screen slot index as 3 rows of 5 [1]-15\n' +
                  'For absolute x,y positioning use --position'))
        parser.add_argument('--log_level', '-ll', type=int,
            choices=[10, 20, 30, 40, 50], default=logging.INFO,
            help=("Set the logging level "
                  "10:DEBUG, 20:INFO, 30:WARN, 40:ERROR, 50:CRITICAL [20:INFO]"))
        #parser.add_argument('--log_qos', action=argparse.BooleanOptionalAction,
            #help="Log the QoS for all participants at log level INFO [no-log-qos]")
        parser.add_argument('--log_qos', default=logging.DEBUG, type=int,
            help="Log the QoS for all participants at the passed log level [10:DEBUG]")
        parser.add_argument('--position', '-p', default=None, nargs=2, metavar=('x' 'y'), type=int,
            help=('Specify the screen position in pixels as two integers\n' +
                  'For simpler slot placement, use --index'))
        parser.add_argument('--publish_rate', '-pr', default=20, type=int,
            help='Specify the delay between screen updates in milliseconds [20]')
        parser.add_argument('--qos_file', '-qf', type=str, default=self.default_dic['QOS_FILE'],
            help=f"Specify the full path of a QoS file [{self.default_dic['QOS_FILE']}]")
        parser.add_argument('--qos_lib', '-ql', type=str, default=self.default_dic['QOS_LIB'],
            help=f"Specify the QoS library name [{self.default_dic['QOS_LIB']}]")
        parser.add_argument('--qos_profile', '-qp', type=str,
            default=self.default_dic['QOS_PROFILE'],
            help=f"Specify the QoS profile name [{self.default_dic['QOS_PROFILE']}]")
        parser.add_argument('--subtitle', '-st', type=str, default="",
            help='Provide a subtitle to the widget [""]')
        parser.add_argument('--title', '-t', type=str, default=self.default_dic['TITLE'],
            help=f"Provide a title to the widget [{self.default_dic['TITLE']}]")
        parser.add_argument('--ticks', action=argparse.BooleanOptionalAction,
            help='Show tick marks on axes [False]')

        parser.add_argument('--subscribe', '-sub', type=validate_shape_letters, default="S",
            help='Start a simple subscriber to any or all of Circle, Square, Triangle [S]')

        parser.add_argument('--publish', '-pub', type=validate_shape_letters,  ## default="S"
            help=('Start a simple publisher of Circle, Square, and/or Triangle ' +
                  '[no default, must select]'))

        # internal args used whilst developing/debugging only
        parser.add_argument('--justdds', '-j', type=int,
            help='just call dds draw this many times, no graphing, for testing')
        parser.add_argument('--nap', '-n', type=float, default=0, # nargs='+',
            help=('intrasample naptime in milliseconds'))
            # 'specify multiple params for a repeating sequence of naps [default:1000.0]'))

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
                if args.index <= 15 and args.index >= 1:
                    args.position = args.index
                else:
                    raise ValueError(f'--index value must be 1-15 not {args.index}')

        return args
