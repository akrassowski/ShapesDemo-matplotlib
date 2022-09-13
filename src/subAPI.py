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
import os
import sys
import time

# animation imports
import matplotlib
if os.name != 'nt':
    matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# Connext imports
import rti.connextdds as dds

# helper class
from MPLShape import MPLShape
from Sample import Sample

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.INFO)

def correctAspect(axes):
    """needed for round circles"""
    axes.set_aspect(1.0/axes.get_data_ratio()*1.0)
    return axes


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

def init_dds(domain_id, extended=True):
    """return reader_dic """
    LOG.debug(f'init_dds {domain_id=} {extended=}')
    reader_dic = {}
    participant = dds.DomainParticipant(domain_id) 
    subscriber = dds.Subscriber(participant)

    qos_file = os.path.dirname(os.path.realpath(__file__)) + "/SimpleShapeExample.xml"
    provider = dds.QosProvider(qos_file)

    type_name = "ShapeTypeExtended" if extended else "ShapeType"
    provider_type = provider.type(type_name)

    circle_topic = dds.DynamicData.Topic(participant, "Circle", provider_type)
    square_topic = dds.DynamicData.Topic(participant, "Square", provider_type)
    triangle_topic = dds.DynamicData.Topic(participant, "Triangle", provider_type)


    # DataReader QoS is configured in USER_QOS_PROFILES.xml
    reader_dic['C'] = dds.DynamicData.DataReader(subscriber, circle_topic)
    reader_dic['S'] = dds.DynamicData.DataReader(subscriber, square_topic)
    reader_dic['T'] = dds.DynamicData.DataReader(subscriber, triangle_topic)

    return reader_dic

    
def main(args):

    poly_dic = {}
    old_samples = {'C': [], 'S': [], 'T': []}

    fig, axes = create_matplot(args, f"ShapeSubscriber Domain:{args.domain_id} Slot: {args.index}")
    # fig.suptitle("")

    reader_dic = init_dds(args.domain_id, args.extended)

    def _get_sample_id(sample):
        """given a sample, return the guid and a guid-qualified sample id"""
        guid = str(sample.info.source_guid)
        seq = sample.info.reception_sequence_number.value
        return guid, (guid, seq)
    
    def _process_sample(sample, which):
        if args.justdds:
            return

        if sample:
            d = sample.data
            LOG.debug(f'SAMPLE: {d.color=} {d.x=}')
            guid, sample_id = _get_sample_id(sample)
            mpl_shape = MPLShape(args, which, sample)
            poly = poly_dic.get(guid)
            if not poly:
                if args.justdds:
                    poly = None
                else:
                    poly = mpl_shape.create_poly()
                poly_dic[guid] = poly
                LOG.info(f'added {guid=}, {mpl_shape.color=}')
                if not args.justdds:
                    axes.add_patch(poly)

            LOG.debug(f'got {sample_id=} \n{poly_dic.values()=}')
            xy = mpl_shape.get_points()
            if which == 'CP':
                poly.center = xy
                # no such attribute poly.set_xy(xy)
                # no such property center poly.set(center=xy)
            elif which == 'C':
                poly.set(center=xy)
            else:
                poly.set_xy(xy)


    def do_read(reader, which):
        """handle the sample input, return the list of shapes"""
        LOG.debug(f'{which=} {old_samples[which]=} ')

        # select any leftover samples then first of new take()
        my_sample = {}
        if len(old_samples[which]) > 0:
            my_sample = old_samples[which].pop()
        else:
            with reader.read_valid() as samples:
                first = True
                for sample in samples:
                    LOG.debug(f'{first=} {sample=} ')
                    if first:
                        LOG.debug(f'{sample.info=} {sample.data=}')
                        my_sample = Sample(sample)
                        first = False
                    else:
                        old_samples[which].append(Sample(sample))
                        LOG.debug(f'ADDED {old_samples=}')
        LOG.debug(f'{my_sample=}')
        """if my_sample:
            d = my_sample.data
            LOG.info(f'SAMPLE {d.x=} {d.y=} {d.color=}')"""

        _process_sample(my_sample, which)
 

    def read_and_draw(_frame):
        """The animation function, called periodically in a set interval, reads the
        last image received and draws it"""
        #####if _frame > 3: sys.exit(0)
        # The Qos configuration guarantees we will only have the last sample;
        # we read (not take) so we can access it again in the next interval if
        # we don't receive a new one
        readers = reader_dic.values()
        whiches = reader_dic.keys()
        for reader, which in zip(readers, whiches):
            #LOG.info(f'FOR READERS {which=} {len(readers)=}')
            do_read(reader, which)

        return poly_dic.values()  # give back the updated values so they are rendered


    if args.justdds:
        LOG.info(f'RUNNING {args.justdds=} reads')
        for i in range(args.justdds):
            read_and_draw(10)
            LOG.info(f'{i=} of {args.justdds=}')
            time.sleep(0.001)
        sys.exit(0)

    # Create the animation and show
    else:
        LOG.debug("Calling FuncAnimation which calls read_and_draw")
        ani = FuncAnimation(fig, read_and_draw, interval=10, blit=False)

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

    parser.add_argument('--domain_id', '-d', type=int, default=0, 
        help='Specify Domain on which to listen [0]-122')

    parser.add_argument('--justdds', '-j', type=int,
        help='just call dds draw this many times, no graphing, for testing')

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

    # Catch control c interrupt
    try:
        main(args)
    except KeyboardInterrupt:
        LOG.info("all done")

## No need for --extended, subscriber just uses extended type
