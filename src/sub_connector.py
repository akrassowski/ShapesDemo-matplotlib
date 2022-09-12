#!/usr/bin/env python

###############################################################################
# (c) Copyright, Real-Time Innovations, 2019. All rights reserved.            #
# No duplications, whole or partial, manual or electronic, may be made        #
# without express written permission.  Any such copies, or revisions thereof, #
# must display this notice unaltered.                                         #
# This code contains trade secrets of Real-Time Innovations, Inc.             #
###############################################################################

"""Reads Shapes and displays them"""


# python imports
import argparse
import logging
import math
from os import path as os_path
import sys
import time

# animation imports
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# Connext imports
import rticonnextdds_connector as rti

# helper class
from MPLShape import MPLShape


# 
LOG = logging.getLogger(__name__)


def get_file_path():
    """return the current directory"""
    return os_path.dirname(os_path.realpath(__file__))

def correctAspect(axes):
    """needed for round circles"""
    axes.set_aspect(1.0/axes.get_data_ratio()*1.0)
    return axes


def get_sample_id(sample):
    """given a sample, return the guid and a guid-qualified sample id"""
    id =  sample.info['identity']
    guid = ''.join(str(x) for x in id['writer_guid'])
    return guid, (guid, id['sequence_number'])
    

def create_matplot(args, name):
    """init all the figure attributes - some is Mac-specific, some must be done b4 creating fig"""
    """ taken from https://stackoverflow.com/questions/7449585/how-do-you-set-the-absolute-position-of-figure-windows-with-matplotlib """

    # turn off toolbar - do this FIRST
    matplotlib.rcParams['toolbar'] = 'None'

    # create the Figure - SECOND
    fig, axes = plt.subplots(figsize=args.figureXY, num=name)
    ##fig.suptitle("awaiting data...")
    axes.set_xlim((0, args.graphx))
    axes.set_ylim((0, args.graphy))
    axes.get_xaxis().set_visible(False)
    axes.get_yaxis().set_visible(False)
    # remove margin
    plt.subplots_adjust(left=0, bottom=0, right=1, top=1, wspace=0, hspace=0)

    # get the x, y, dx, dy
    mngr = plt.get_current_fig_manager()
    x, y, dx, dy = mngr.window.geometry().getRect()
    HGAP, VGAP = 30, 85
    Y, HSP = VGAP + dy, HGAP+5
    coord = [ (0, 0), (dx+HGAP, 0), (2*dx+HSP, 0), (0, Y), (dx+HGAP, Y), (2*dx+HSP, Y) ]
    x, y = coord[args.index-1]
    LOG.debug(f'{x=}, {y=}')
    mngr.window.setGeometry(x, y, int(dx), int(dy))

    return fig, axes

def main(args):

    fig, axes = create_matplot(args, f"ShapeSubscriber {args.index}")

    qos_file = os_path.dirname(os_path.realpath(__file__)) + "/SimpleShapeExample.xml"
    with rti.open_connector(
            config_name="MyParticipantLibrary::MySubParticipant",
            url=get_file_path() + "/SimpleShapeExample.xml") as connector:

        global handle_input_count
        handle_input_count = 0
        def handle_input(input, which='T'):
            """handle the sample input, return the list of shapes"""
            global handle_input_count
            input.read()
            #input.take()
            last_id = (-1, -1) 
            handle_input_count += 1
            sample_count = 0
            for sample in input.samples.valid_data_iter:
                sample_count += 1
                if handle_input_count < 10:
                    LOG.info(f'SAMPLE == {sample.get_dictionary()=}')
                guid, sample_id = get_sample_id(sample)
                mpl_shape = MPLShape(args, which, sample.get_dictionary(), connector_mode=True)
                poly = poly_dic.get(guid)
                if not poly:
                    poly = mpl_shape.create_poly()
                    poly_dic[guid] = poly
                    LOG.info(f'added {guid=}, {mpl_shape.color=}')
                    axes.add_patch(poly)

#TODO - no need to change xy if stuck on last seq#
                LOG.debug(f'moving to {sample_id=} \n{poly_dic.values()=}')
                xy = mpl_shape.get_points()
                if which == 'CP':
                    poly.center = xy
                    # no such attribute poly.set_xy(xy)
                    # no such property center poly.set(center=xy)
                elif which == 'C':
                    poly.set(center=xy)
                else:
                    poly.set_xy(xy)
                if sample_id == last_id:
                    poly.set(fc='k')
                else:
                    last_id = sample_id

            LOG.debug(f'{sample_count=}')
            #time.sleep(10)
            return poly_dic.values()


        poly_dic = {}

        connector.wait() #- Avoid creating placeholder shape
        ## input.wait() - operates on just this input
        fig.suptitle("")

        my_shapes = ["Circle", "Square", "Triangle"]
        my_whiches = [str(w[0]) for w in my_shapes]
        ## try CP but doesn't animate my_whiches[0] = 'CP'
        inputs = [connector.get_input(f"MySubscriber::My{shape}Reader") for shape in my_shapes]

        def read_and_draw(_frame):
            """The animation function, called periodically in a set interval, reads the
            last image received and draws it"""
            #####if _frame > 3: sys.exit(0)
            # The Qos configuration guarantees we will only have the last sample;
            # we read (not take) so we can access it again in the next interval if
            # we don't receive a new one
            for inpt, which in zip(inputs, my_whiches):
                handle_input(inpt, which)

            return poly_dic.values()  # give back the updated values so they are rendered

        # Create the animation and show
        LOG.debug("Calling FuncAnimation which calls read_and_draw")
        ani = FuncAnimation(fig, read_and_draw, interval=20, blit=True)
        ##ani = FuncAnimation(fig, read_and_draw, interval=20, blit=False)

        # Show the image and block until the window is closed
        plt.show()
        LOG.info("Exiting...")

def parse_args(args):
    """pass args to allow testing"""
    FIGX, FIGY = 4, 4
    MAXX, MAXY = 240, 270
    parser = argparse.ArgumentParser(description="Simple ShapesDemo Subscriber")
    parser.add_argument('-f', '--figureXY', default=(FIGX, FIGY), type=int, nargs=2,
        help=f'x,y of figure in inches [{FIGX},{FIGY}]')
    parser.add_argument('-g', '--graphXY', default=(MAXX, MAXY), type=int, nargs=2,
        help=f'width and height of graph in pixels [{MAXX},{MAXY}]')
    parser.add_argument('-l', '--level', type=int, help="logger level [4=INFO]")
    parser.add_argument('-i', '--index', type=int, default=1,
        help=f'slot index [1]-6')

    parser.add_argument('--extended', action=argparse.BooleanOptionalAction, 
        help='Use ShapeTypeExtended [ShapeType]')

    args = parser.parse_args()
#    args.figxy = args.figureXY[0], args.figureXY[1]
    args.graphx, args.graphy = args.graphXY[0], args.graphXY[1]
    LOG.info(f'{args=}')
    return args
    

if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)-15s [%(levelname)s] %(funcName)s: %(message)s",
        level=logging.INFO)
    args = parse_args(sys.argv)
    main(args)

## No need for --extended, subscriber just uses extended type
