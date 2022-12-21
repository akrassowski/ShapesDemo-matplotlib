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
import logging
import sys

# application imports
from ArgParser import ArgParser
from ConfigParser import ConfigParser
from Connext import get_cwd
from ConnextPublisher import ConnextPublisher
from ConnextSubscriber import ConnextSubscriber
from MatplotlibWrapper import MatplotlibWrapper

LOG = logging.getLogger(__name__)

DEFAULT_DIC = {
    'COLOR': 'BLUE',
    'DOMAIN_ID': 0,
    'FIG_XY': (2.375, 2.72),  # match RTI ShapesDemo box size
    'MAX_XY': (240, 270),
    'QOS_FILE': './SimpleShape.xml',
    'QOS_LIB': 'MyQosLibrary',
    'QOS_PROFILE': 'MyProfile',
    'TITLE': 'Shapes'
}


def handle_config_help_and_exit():
    """print the defaults and exit"""

    def _print_defaults(msg, value_dic, help_dic):
        print(msg)
        for key, value in value_dic.items():
            # avoid trailing default if [] in help already
            display_value = "" if "[" in help_dic[key] else f' [{value}]'
            print(f'{str.rjust(key, 25)}: {help_dic[key]}{display_value}')
        print('\n')

    parser = ConfigParser(DEFAULT_DIC)
    pub_dic_defaults, pub_dic_help = parser.get_pub_config(True)
    sub_dic_defaults, sub_dic_help = parser.get_sub_config(True)
    _print_defaults('Subscriber values and [default]:', sub_dic_defaults, sub_dic_help)
    _print_defaults('Publisher values and [default]:', pub_dic_defaults, pub_dic_help)
    sys.exit(0)


def get_connext_obj_or_die(args):
    """create either a Publisher or a Subscriber from config"""
    parser = ConfigParser(DEFAULT_DIC)
    parser.parse(args.config)
    args, is_pub, config = parser.get_config(args)
    return ConnextPublisher(args, config) if is_pub else ConnextSubscriber(args, config)


def handle_justdds(args, connext_obj):
    """For debugging, run some callbacks"""
    LOG.info('RUNNING args.justdds=%d reads', args.justdds)
    for i in range(args.justdds):
        connext_obj.draw(10)
        LOG.info('%d of %d', i, args.justdds)

def main(args):
    """MAIN ENTRY POINT"""
    if args.config_help:
        handle_config_help_and_exit()

    connext_obj = get_connext_obj_or_die(args)

    if args.justdds:
        handle_justdds(args, connext_obj)
        sys.exit(0)

    #cwd = os.path.dirname(os.path.realpath(__file__))
    cwd = get_cwd(__file__)
    image_filename = f'{cwd}/RTI_Logo_RGB-Color.png'

    box_title = f"Shapes Domain:{args.domain_id}" \
        if args.title == DEFAULT_DIC['TITLE'] else args.title
    fig, axes, plt = MatplotlibWrapper.create_matplot(
        args.figure_xy, args.graph_xy, image_filename, box_title, args.index, args.subtitle
    )

    connext_obj.start(fig, axes)
    # lower interval if updates are jerky
    unused_ref = MatplotlibWrapper.func_animation(fig, connext_obj.draw, interval=20, blit=True)
    # Show the image and block until the window is closed
    plt.show()
    LOG.info("Exiting...")


if __name__ == "__main__":
    p_args = ArgParser(DEFAULT_DIC).parse_args(sys.argv[1:])
    TIME_FMT = '%(asctime)s,%(msecs)03d '
    logging.basicConfig(
        format=TIME_FMT + '%(levelname)s %(filename)s-%(funcName)s:%(lineno)d %(message)s',
        datefmt='%m-%d %H:%M:%S',
        level=p_args.log_level)

    # Catch control c interrupt
    try:
        main(p_args)
    except KeyboardInterrupt:
        LOG.info("all done")

# No need for --extended, subscriber just uses extended type
