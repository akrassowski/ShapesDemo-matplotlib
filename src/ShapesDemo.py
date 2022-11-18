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
import os
from pprint import pprint
import sys

try:
# animation imports
    import matplotlib
# TODO - use Qt5 if not on PC
    if os.name != 'nt':
        matplotlib.use('Qt5Agg')  # must precede pyplot
    import matplotlib.pyplot as plt
    from matplotlib.animation import FuncAnimation
except:
    print("No matplotlib")


# Connext imports
from ArgParser import ArgParser
from ConfigParser import ConfigParser
from Connext import Connext
from ConnextPublisher import ConnextPublisher
from ConnextSubscriber import ConnextSubscriber


LOG = logging.getLogger(__name__)

DEFAULT_TITLE = "Shapes"


def create_matplot(args):
    """init all the figure attributes - some is Mac-specific, some must be done b4 creating fig"""
    """ taken from https://stackoverflow.com/questions/7449585/how-do-you-set-the-absolute-position-of-figure-windows-with-matplotlib """

    box_title = f"Shapes Domain:{args.domain_id}" if args.title == DEFAULT_TITLE else args.title

    # turn off toolbar - do this FIRST
    matplotlib.rcParams['toolbar'] = 'None'

    # create the Figure - SECOND
    fig, axes = plt.subplots(figsize=args.figureXY, num=box_title)
    axes.set_xlim((0, args.graphx))
    axes.set_ylim((0, args.graphy))

    # add a requested subtitle
    if args.subtitle:
        fig.suptitle(args.subtitle)

    # hide the axis ticks/subticks/labels
    axes.get_xaxis().set_visible(False)
    axes.get_yaxis().set_visible(False)

    # remove margin
    plt.subplots_adjust(left=0, bottom=0, right=1, top=1, wspace=0, hspace=0)

    # Compute the Slots when running multiple instances
    # get the x, y, dx, dy
    mngr = plt.get_current_fig_manager()
    x, y, dx, dy = mngr.window.geometry().getRect()
    HGAP, VGAP = 30, 85
    Y, HSP = VGAP + dy, HGAP+5
    coord = [(0, 0), (dx+HGAP, 0), (2*dx+HSP, 0),
             (0, Y), (dx+HGAP, Y), (2*dx+HSP, Y)]
    x, y = coord[args.index-1]
    LOG.debug(f'{x=}, {y=}')
    mngr.window.setGeometry(x, y, int(dx), int(dy))

    # set a background image  # TODO scale when resizing or specify "center"?
    cwd = Connext.get_cwd(__file__)
    image = plt.imread(f'{cwd}/RTI_Logo_RGB-Color.png')
    fig.figimage(image, xo=35, yo=120, zorder=3, alpha=0.1)

    return fig, axes


def handle_config_help(args):
    """print the defaults and exit"""

    def _print_defaults(msg, value_dic, help_dic):
        print(msg)
        for key, value in value_dic.items():
            print(f'{str.rjust(key, 25)}: {help_dic[key]} [{value}]')
        print('\n')

    parser = ConfigParser(args.config)
    pub_dic_defaults, pub_dic_help = parser.get_pub_config(True)
    sub_dic_defaults, sub_dic_help = parser.get_sub_config(True)
    _print_defaults('Subscriber values and [default]:', sub_dic_defaults, sub_dic_help)
    _print_defaults('Publisher values and [default]:', pub_dic_defaults, pub_dic_help)


def get_connext_obj_or_die(args):
    """create either a Publisher or a Sub from config or command-line"""
    connext_obj = None
    parser = ConfigParser(args.config)
    if args.config:
        pub_cfg = parser.get_pub_config()
        sub_cfg = parser.get_sub_config()
        LOG.info(f'{pub_cfg=} {sub_cfg=}') 
        if pub_cfg and sub_cfg:
            LOG.warning("Both pub and sub found, ignoring publisher")
        if sub_cfg:
            connext_obj = ConnextSubscriber(args, sub_cfg)
        elif pub_cfg:
            connext_obj = ConnextPublisher(args, pub_cfg)
    ## config OR command-line - sub OR pub only 
    elif args.subscribe:
        sub_cfg = {}
        for which in args.subscribe:
            defaults, _ = parser.get_sub_config(default=True)
            sub_cfg[which] = defaults
        connext_obj = ConnextSubscriber(args, sub_cfg)
    elif args.publish:
        connext_obj = ConnextPublisher(args)
    else:
        LOG.error("Must run as either publisher or subscriber, terminating")
        sys.exit(-1)
    return connext_obj


def handle_justdds(args, connext_obj):
    """For debugging, run some callbacks"""
    LOG.info(f'RUNNING {args.justdds=} reads')
    for i in range(args.justdds):
        connext_obj.fetch_and_draw(10)
        LOG.info(f'{i} of {args.justdds}')
    
def main(args):

    if args.config_help:
        handle_config_help(args)
        sys.exit(0)

    connext_obj = get_connext_obj_or_die(args)

    if args.justdds:
        handle_justdds(args, connext_obj)
        sys.exit(0)

    # Create the animation and show
    fig, axes = create_matplot(args)

    connext_obj.start(fig, axes)
    # lower interval if updates are jerky
    ani = FuncAnimation(fig, connext_obj.fetch_and_draw, interval=20, blit=True )

    # Show the image and block until the window is closed
    plt.show()
    LOG.info("Exiting...")


if __name__ == "__main__":
    args = ArgParser().parse_args(sys.argv, DEFAULT_TITLE)
    logging.basicConfig(
        format="%(asctime)-15s [%(levelname)s] %(funcName)s: %(message)s",
        level=args.log_level)
    
    # Catch control c interrupt
    try:
        main(args)
    except KeyboardInterrupt:
        LOG.info("all done")

# No need for --extended, subscriber just uses extended type

"""
OPTIONS
  Shape - C, S, T
  
  SUB-only
    sleep
    history depth (QoS)

  PUB-only
    Color - 1 of 8
    size
    angle
    fill
    delta xy
    delta angle


{ 'triangle': {
  'color': red
  size: 30,
  fill: none
  angle: 



CR
"""
