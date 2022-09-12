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
import rti.connextdds as dds

# helper class
from MPLShape import MPLShape

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)

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

    #qos_file = os_path.dirname(os_path.realpath(__file__)) + "/ShapeTypeExtended.xml"
    qos_file = os_path.dirname(os_path.realpath(__file__)) + "/SimpleShapeExample.xml"
    provider = dds.QosProvider(qos_file)

    type_name = "ShapeTypeExtended" if extended else "ShapeType"
    provider_type = provider.type(type_name)

    square_topic = dds.DynamicData.Topic(participant, "Square", provider_type)
    triangle_topic = dds.DynamicData.Topic(participant, "Triangle", provider_type)


    # DataReader QoS is configured in USER_QOS_PROFILES.xml
    reader_dic['S'] = dds.DynamicData.DataReader(subscriber, square_topic)
    reader_dic['T'] = dds.DynamicData.DataReader(subscriber, triangle_topic)

    r = reader_dic['S']
    with r.read() as samples:
        for s in samples:
            LOG.info(f'{s=}')

    return reader_dic

    
def main(args):

    poly_dic = {}

    # fig.suptitle("")

    reader_dic = init_dds(args.domain_id, args.extended)

    def _get_sample_id(sample):
        """given a sample, return the guid and a guid-qualified sample id"""
        guid = str(sample.info.source_guid)
        seq = sample.info.reception_sequence_number.value
        return guid, (guid, seq)
    
    def _process_sample(sample, which):
        global handle_input_count
        if handle_input_count < 10 and sample:
            d = sample.data
            #breakpoint()
            LOG.info(f'SAMPLE: {d["color"]=} {d["x"]=}')
        if sample and sample.info.valid:
            guid, sample_id = _get_sample_id(sample)
            mpl_shape = MPLShape(args, which, sample)
            poly = poly_dic.get(guid)
            if not poly:
                poly = mpl_shape.create_poly()
                poly_dic[guid] = poly
                LOG.info(f'added {guid=}, {mpl_shape.color=}')
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

        #LOG.debug(f'{sample_count=}')
        #time.sleep(1)
        LOG.info(f'return {poly_dic.values()=}')
        return poly_dic.values()

    if 1 == 1:
        global handle_input_count, old_samples
        handle_input_count = 0
        old_samples = {'C': [], 'S': [], 'T': []}

        def do_read(reader, which):
            """handle the sample input, return the list of shapes"""
            global handle_input_count, old_samples
            handle_input_count += 1
            LOG.info(f'{which=} {old_samples[which]=} ')
            if handle_input_count > 100: 
                sys.exit(0)

            # select any leftover samples then first of new take()
            my_sample = None
            if len(old_samples[which]) > 0:
                my_sample = old_samples[which].pop()
            else:
                with reader.read() as samples:
                    first = True
                    for sample in samples:
                        LOG.info(f'{first=} {sample=} ')
                        if first:
                            my_sample = sample
                            first = False
                        else:
                            old_samples[which].append(sample)
                            LOG.info(f'ADDED {old_samples=}')
            if my_sample:
                d = my_sample.data
                LOG.info(f'SAMPLE {d["x"]=} {d["y"]=} {d["color"]=}')
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


    ### inline test
    time.sleep(5)
    rdr = reader_dic['S']
    with rdr.take() as samples:
        for s in samples:
            print(s)
            if s.info.valid:
                print(f'{s.data["x"]=} {s.data["color"]=}')
            else:
                print('invalid')

    fig, axes = create_matplot(args, f"ShapeSubscriber Domain:{args.domain_id} {args.index}")

 
    '''if args.dds:
        for i in range(args.dds):
            read_and_draw(10)
            time.sleep(0.01)
        sys.exit(0)'''

    # Create the animation and show
    LOG.debug("Calling FuncAnimation which calls read_and_draw")
    ani = FuncAnimation(fig, read_and_draw, interval=20, blit=False)

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

    parser.add_argument('--dds', '-1', type=int,
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
