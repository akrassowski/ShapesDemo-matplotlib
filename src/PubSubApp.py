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
import sys

# animation imports
import matplotlib
# TODO - use Qt5 if not on PC
if os.name != 'nt':
    matplotlib.use('Qt5Agg')  # must precede pyplot
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# Connext imports
from ConnextPub import ConnextPub
from ConnextSub import ConnextSub

from ArgParser import parse_args

LOG = logging.getLogger(__name__)

DEFAULT_TITLE = "Shapes"


def create_matplot(args, box_title):
    """init all the figure attributes - some is Mac-specific, some must be done b4 creating fig"""
    """ taken from https://stackoverflow.com/questions/7449585/how-do-you-set-the-absolute-position-of-figure-windows-with-matplotlib """

    # turn off toolbar - do this FIRST
    matplotlib.rcParams['toolbar'] = 'None'

    # create the Figure - SECOND
    fig, axes = plt.subplots(figsize=args.figureXY, num=box_title)
    axes.set_xlim((0, args.graphx))
    axes.set_ylim((0, args.graphy))

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
    image = plt.imread("RTI_Logo_RGB-Color.png")
    fig.figimage(image, xo=35, yo=120, zorder=3, alpha=0.1)

    return fig, axes


def main(args):

    if args.title == DEFAULT_TITLE:
        title = f"Shapes Domain:{args.domain_id}"
    else:
        title = args.title
    fig, axes = create_matplot(args, box_title=title)

    if args.subtitle:
        fig.suptitle(args.subtitle)

    connext_obj = None
    if args.subscribe:
        connext_obj = ConnextSub(args)
    elif args.publish:
        connext_obj = ConnextPub(args)
    else:
        print("Must run as either publisher or subscriber")
        sys.exit(-1)

    if args.justdds:
        LOG.info(f'RUNNING {args.justdds=} reads')
        for i in range(args.justdds):
            fetch_and_draw(10)
            LOG.info(f'{i} of {args.justdds}')
        sys.exit(0)

    # Create the animation and show
    else:
        # lower interval if updates are jerky
        connext_obj.start(fig, axes)
        ani = FuncAnimation(fig, connext_obj.fetch_and_draw, interval=20, blit=True )

        # Show the image and block until the window is closed
        plt.show()
    LOG.info("Exiting...")


if __name__ == "__main__":
    args = parse_args(sys.argv, DEFAULT_TITLE)
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
