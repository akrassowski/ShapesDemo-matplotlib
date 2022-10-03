#!/usr/bin/env python

###############################################################################
# (c) Copyright, Real-Time Innovations, 2021. All rights reserved.            #
# No duplications, whole or partial, manual or electronic, may be made        #
# without express written permission.  Any such copies, or revisions thereof, #
# must display this notice unaltered.                                         #
# This code contains trade secrets of Real-Time Innovations, Inc.             #
###############################################################################

"""Reads Shapes and displays them"""


# python imports
import argparse
import logging
import os
import sys
import time

# animation imports
import matplotlib
# TODO - use Qt5 if not on PC
if os.name != 'nt':
    matplotlib.use('Qt5Agg')  # must precede pyplot
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# Connext imports
import rti.connextdds as dds

# helper class
from Shape import Shape

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.INFO)

WIDE_EDGE_LINE_WIDTH, THIN_EDGE_LINE_WIDTH = 3, 1


def create_matplot(args, box_title):
    """init all the figure attributes - some is Mac-specific, some must be done b4 creating fig"""
    """ taken from https://stackoverflow.com/questions/7449585/how-do-you-set-the-absolute-position-of-figure-windows-with-matplotlib """

    # turn off toolbar - do this FIRST
    matplotlib.rcParams['toolbar'] = 'None'

    # create the Figure - SECOND
    fig, axes = plt.subplots(figsize=args.figureXY, num=box_title)
    ##fig.suptitle("awaiting data...")
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

    # set a background image
    image = plt.imread("RTI_Logo_RGB-Color.png")
    fig.figimage(image, xo=35, yo=120, zorder=3, alpha=0.1)
    #MARX, MARY = 25, 55
    #image = axes.imshow(image, extent=[MARX, args.graphx-MARX, MARY, args.graphy-MARY])

    return fig, axes


def init_dds(domain_id, qos_file, qos_lib, qos_profile, extended=True):
    """return reader_dic and info_dic"""  # TODO add Pubs here
    LOG.info(f'init_dds {domain_id=} {qos_file} {extended=}')
    participant = dds.DomainParticipant(domain_id)
    subscriber = dds.Subscriber(participant)

    provider = dds.QosProvider(qos_file, "MyQosLibrary::MyProfile")

    type_name = "ShapeTypeExtended" if extended else "ShapeType"
    provider_type = provider.type(type_name)

    circle_topic = dds.DynamicData.Topic(participant, "Circle", provider_type)
    square_topic = dds.DynamicData.Topic(participant, "Square", provider_type)
    triangle_topic = dds.DynamicData.Topic(
        participant, "Triangle", provider_type)

    reader_qos = provider.datareader_qos
    circle_reader = dds.DynamicData.DataReader(
        subscriber, circle_topic, reader_qos)
    square_reader = dds.DynamicData.DataReader(
        subscriber, square_topic, reader_qos)
    triangle_reader = dds.DynamicData.DataReader(
        subscriber, triangle_topic, reader_qos)

    reader_dic = {
        'C': circle_reader,
        'S': square_reader,
        'T': triangle_reader,
    }
    info_dic = {
        'C': circle_reader.qos.resource_limits.max_samples_per_instance, 'CI': 0,
        'S': square_reader.qos.resource_limits.max_samples_per_instance, 'SI': 0,
        'T': triangle_reader.qos.resource_limits.max_samples_per_instance, 'TI': 0,
    }

    return reader_dic, info_dic


class InstanceGen:
    """returns instance number confined to the range"""

    def __init__(self, number):
        self.number = number
        self.at = 0
        self.instance = 0

    def at(self):
        """return the last given number"""
        return self.at

    def get_prev_ix(self):
        return (self.at - 1 + self.number) % self.number

    def next(self):
        self.at = self.instance
        self.instance = (self.instance + 1) % self.number
        return self.at


def form_instance_gen_key(topic_letter, color):
    return f'{topic_letter}-{color}'


def form_poly_key(which, color, instance_num):
    return f'{which}-{color}-{instance_num}'


def main(args):

    poly_dic = {}  # all polygon instances keyed by Topic+Color+InstanceNum
    #poly_list = []

    # keep shape dic for each Topic holding list of instances
    #shapes = {'C': defaultdict(list), 'S': defaultdict(list), 'T': defaultdict(list)}
    shapes = {'C': {}, 'S': {}, 'T': {}}
    instance_gen_dic = {}  # Topic-color: InstanceGen

    title = f"ShapeSubscriber Domain:{args.domain_id} Slot: {args.index}"
    fig, axes = create_matplot(args, box_title=title)

    # fig.suptitle("")
    cwd = os.path.dirname(os.path.realpath(__file__))

    reader_dic, info_dic = init_dds(
        domain_id=args.domain_id,
        qos_file=cwd +
        args.qos_file[1:] if args.qos_file[0] == '.' else args.qos_file,
        qos_lib=args.qos_lib,
        qos_profile=args.qos_profile,
        extended=args.extended
    )

    def handle_one_sample(which, sample):
        """update the poly_dic with fresh shape info"""
        """create/update a matplotlib polygon from the sample data, add to poly_dic
           remove the prior poly's edge"""
        shape = Shape(args=args, which=which,
                      data=sample.data, info=sample.info)
        instance_gen_key = form_instance_gen_key(
            which, shape.scolor)  # use API to get Key
        inst = instance_gen_dic.get(instance_gen_key)
        if not inst:
            inst = InstanceGen(info_dic[which])
            instance_gen_dic[instance_gen_key] = inst
        ix = inst.next()
        LOG.debug(f"SHAPE: {shape=}, {ix=}")
        poly_key = form_poly_key(which, shape.scolor, ix)
        poly = poly_dic.get(poly_key)
        if args.justdds:
            LOG.info("early exit")
            return
        if not poly:
            poly = shape.create_poly()
            poly_dic[poly_key] = poly
            LOG.info(f"added {poly_key=}")
            axes.add_patch(poly)

        xy = shape.get_points()
        if which == 'CP':
            poly.center = xy
            # no such attribute poly.set_xy(xy)
            # no such property center poly.set(center=xy)
        elif which == 'C':
            poly.set(center=xy)
        else:
            poly.set_xy(xy)
        poly.set(lw=WIDE_EDGE_LINE_WIDTH, zorder=shape.zorder)

        prev_poly_key = form_poly_key(which, shape.scolor, inst.get_prev_ix())
        prev_poly = poly_dic.get(prev_poly_key)
        if prev_poly:
            prev_poly.set(lw=THIN_EDGE_LINE_WIDTH)

    def handle_samples(reader, which):
        """get samples and handle each"""

        with reader.take_valid() as samples:
            for sample in samples:
                handle_one_sample(which, sample)

        if args.nap:
            time.sleep(args.nap)
            LOG.info(f'Sleeping {args.nap=}')

    def fetch_and_draw(_frame):
        """The animation function, called periodically in a set interval, reads the
        last image received and draws it"""
        readers = reader_dic.values()
        whiches = reader_dic.keys()
        for reader, which in zip(readers, whiches):
            #LOG.info(f'FOR READERS {which=} {len(readers)=}')
            handle_samples(reader, which)

        return poly_dic.values()  # give back the updated values so they are rendered
        # return poly_list  # give back the updated values so they are rendered

    if args.justdds:
        LOG.info(f'RUNNING {args.justdds=} reads')
        for i in range(args.justdds):
            fetch_and_draw(10)
            LOG.info(f'{i} of {args.justdds}')
        sys.exit(0)

    # Create the animation and show
    else:
        # lower interval if updates are jerky
        ani = FuncAnimation(fig, fetch_and_draw, interval=20, blit=True)
        # Show the image and block until the window is closed
        plt.show()
    LOG.info("Exiting...")


def parse_args(args):
    """pass args to allow testing"""
    FIGX, FIGY = 2.375, 2.72  # match RTI ShapesDemo box size
    MAXX, MAXY = 240, 270
    DEFAULT_QOS_FILE = './SimpleShape.xml'
    DEFAULT_QOS_LIB, DEFAULT_QOS_PROFILE = 'MyQoSLib', 'MyQoSProfile'
    DEFAULT_HISTORY = 6

    parser = argparse.ArgumentParser(
        description="Simple ShapesDemo Subscriber")
    parser.add_argument('--domain_id', '-d', type=int, default=0,
                        help='Specify Domain on which to listen [0]-122')
    parser.add_argument('--extended', action=argparse.BooleanOptionalAction,
                        help='Use ShapeTypeExtended [ShapeType]')
    parser.add_argument('-f', '--figureXY', default=(FIGX, FIGY), type=int, nargs=2,
                        help=f'x,y of figure in inches [{FIGX},{FIGY}]')
    parser.add_argument('-g', '--graphXY', default=(MAXX, MAXY), type=int, nargs=2,
                        help=f'width and height of graph in pixels [{MAXX},{MAXY}]')
    parser.add_argument('-i', '--index', type=int, default=1,
                        help=f'screen slot index [1]-6')
    parser.add_argument('--justdds', '-j', type=int,
                        help='just call dds draw this many times, no graphing, for testing')
    parser.add_argument('-l', '--level', type=int,
                        help="logger level [4=INFO]")
    parser.add_argument('--nap', '-n', type=float, default=0,
                        help=f'intrasample naptime [default:0.0]')
    parser.add_argument('--qos_file', '-qf', type=str, default=DEFAULT_QOS_FILE,
                        help=f'full path of QoS file [{DEFAULT_QOS_FILE}]')
    parser.add_argument('--qos_lib', '-ql', type=str, default=DEFAULT_QOS_LIB,
                        help=f'QoS library name [{DEFAULT_QOS_LIB}]')
    parser.add_argument('--qos_profile', '-qp', type=str, default=DEFAULT_QOS_PROFILE,
                        help=f'QoS profile name [{DEFAULT_QOS_PROFILE}]')
    parser.add_argument('--publish', '-p', type=str,
                        help=f'publish a Shape (Square, Triangle, Circle) \nColor-Speed [Blue-Normal] Colors: Blue, Green, Red, Orange, Magenta, Yellow')

    parser.add_argument('--square-history-depth', '-shd', type=int,
                        help=f'history depth for square topic [{DEFAULT_HISTORY}]')

    args = parser.parse_args()
    args.graphx, args.graphy = args.graphXY
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

# No need for --extended, subscriber just uses extended type
