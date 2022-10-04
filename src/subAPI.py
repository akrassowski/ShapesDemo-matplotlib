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

WIDE_EDGE_LINE_WIDTH, THIN_EDGE_LINE_WIDTH = 2, 1
DEFAULT_TITLE = "Shapes"


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

    # set a background image  # TODO scale when resizing or specify "center"?
    image = plt.imread("RTI_Logo_RGB-Color.png")
    fig.figimage(image, xo=35, yo=120, zorder=3, alpha=0.1)

    return fig, axes


def _init_dds(args):
    participant = dds.DomainParticipant(args.domain_id)
    qos_provider = get_qos_provider(args.qos_file, args.qos_lib, args.qos_profile)

    type_name = "ShapeTypeExtended" if args.extended else "ShapeType"
    provider_type = qos_provider.type(type_name)
    topic_dic = {
        'C': dds.DynamicData.Topic(participant, "Circle", provider_type),
        'S': dds.DynamicData.Topic(participant, "Square", provider_type),
        'T': dds.DynamicData.Topic(participant, "Triangle", provider_type)
    }
    return participant, qos_provider, topic_dic

def get_max_samples_per_instance(reader):
    """ helper to fetch depth from a reader"""
    return reader.qos.resource_limits.max_samples_per_instance

def init_dds_pub(args):
    participant, qos_provider, topic_dic = _init_dds(args)
    #TODO more here
    writer_dic = {
    }
    return writer_dic

def init_dds_sub(args):
    """return reader_dic"""
    participant, qos_provider, topic_dic = _init_dds(args)
    subscriber = dds.Subscriber(participant)
    reader_qos = qos_provider.datareader_qos
    reader_dic = {}
    for which in args.subscribe:
        LOG.info(f'Subscribing to {which} {topic_dic[which]=}')
        reader_dic[which] = dds.DynamicData.DataReader(subscriber, topic_dic[which], reader_qos)
 
    return reader_dic


class InstanceGen:
    """returns instance index confined to the range"""

    def __init__(self, _range):
        self._range = _range
        self.at = 0
        self.instance = 0

    def get_prev_ix(self):
        """return the previous given number with no changes"""
        return (self.at - 1 + self._range) % self._range

    def next(self):
        """return the next instance index and move along"""
        self.at = self.instance
        self.instance = (self.instance + 1) % self._range
        return self.at


def form_poly_key(which, color, instance_num):
    return f'{which}-{color}-{instance_num}'

def get_qos_provider(qos_file, qos_lib, qos_profile):
    """fetch the qos_profile from the lib in the file"""
    cwd = os.path.dirname(os.path.realpath(__file__))
    #  prepend with cwd if starts with dot
    qos_file = cwd + qos_file[1:] if qos_file[0] == '.' else qos_file
    return dds.QosProvider(qos_file, f'{qos_lib}::{qos_profile}')

global sample_count
sample_count = 0
def start_subscriber(args, fig, axes):
    """First, some globals and helpers"""
    poly_dic = {}  # all polygon instances keyed by Topic+Color+InstanceNum
    instance_gen_dic = {}  # Topic-color: InstanceGen
    reader_dic = init_dds_sub(args)

    def handle_one_sample(which, sample):
        """update the poly_dic with fresh shape info"""
        """create/update a matplotlib polygon from the sample data, add to poly_dic
           remove the prior poly's edge"""
        global sample_count
        sample_count += 1
        shape = Shape(args=args, which=which,
                      data=sample.data, info=sample.info)
        instance_gen_key = f'{which}-{shape.scolor}'  # TODO use API to get Key
        inst = instance_gen_dic.get(instance_gen_key)
        if not inst:
            inst = InstanceGen(get_max_samples_per_instance(reader_dic[which]))
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

        LOG.debug(f'START {sample_count=}')
        with reader.take_valid() as samples:
            for sample in samples:
                handle_one_sample(which, sample)

        if args.nap:
            time.sleep(args.nap)
            LOG.info(f'Sleeping {args.nap=}')
        
        LOG.info(f'{sample_count=}')

    def fetch_and_draw(_frame):
        """The animation function, called periodically in a set interval, reads the
        last image received and draws it"""
        readers = reader_dic.values()
        whiches = reader_dic.keys()
        for reader, which in zip(readers, whiches):
            handle_samples(reader, which)

        return poly_dic.values()  # give back the updated values so they are rendered


    if args.justdds:  # just for debugging
        LOG.info(f'RUNNING {args.justdds=} reads')
        for i in range(args.justdds):
            fetch_and_draw(10)
            LOG.info(f'{i} of {args.justdds}')
        sys.exit(0)

    # Create the animation and show
    else:
        # lower interval if updates are jerky
        LOG.info('start animation')
        ani = FuncAnimation(fig, fetch_and_draw, interval=20, blit=True)
        # Show the image and block until the window is closed
        plt.show()

def start_publisher(args, fig, axes):
    print("Publishing is TBD")
    sys.exit(0)

def main(args):

    if args.title == DEFAULT_TITLE:
        title = f"Shapes Domain:{args.domain_id}"
    else:
        title = args.title
    fig, axes = create_matplot(args, box_title=title)

    if args.subtitle:
        fig.suptitle(args.subtitle)

    if args.subscribe:
        start_subscriber(args, fig, axes)
    elif args.publish:
        start_publisher(args, fig, axes)
    else:
        print("Must run as either publisher or subscriber")
        sys.exit(-1)

    LOG.info("Exiting...")


def parse_args(args):
    """pass args to allow testing"""
    FIGX, FIGY = 2.375, 2.72  # match RTI ShapesDemo box size
    MAXX, MAXY = 240, 270
    DEFAULT_QOS_FILE = './SimpleShape.xml'
    DEFAULT_QOS_LIB, DEFAULT_QOS_PROFILE = 'MyQosLibrary', 'MyProfile'
    DEFAULT_HISTORY = 6

    def validate_shape_letters(letters):
        if len(letters) > 3:
            raise ValueError('Cannot subscribe to more then 3 Topics')
        for letter in letters:
            if letter.upper() not in "CST":
                raise ValueError('Topic letters ({letter}) must be one or more of: ' + 
                                 '"CST" for Circle, Square, Triangle')
        return letters.upper()

    parser = argparse.ArgumentParser(
        description="Simple ShapesDemo")
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
    parser.add_argument('-l', '--level', type=int,
                        help="logger level [4=INFO]")
    parser.add_argument('--qos_file', '-qf', type=str, default=DEFAULT_QOS_FILE,
                        help=f'full path of QoS file [{DEFAULT_QOS_FILE}]')
    parser.add_argument('--qos_lib', '-ql', type=str, default=DEFAULT_QOS_LIB,
                        help=f'QoS library name [{DEFAULT_QOS_LIB}]')
    parser.add_argument('--qos_profile', '-qp', type=str, default=DEFAULT_QOS_PROFILE,
                        help=f'QoS profile name [{DEFAULT_QOS_PROFILE}]')
    parser.add_argument('--subtitle', '-st', type=str, default="",
                        help=f'Provide a subtitle to the screen ["Slot n"]')
    parser.add_argument('--title', '-t', type=str, default=DEFAULT_TITLE,
                        help=f'Provide a title to the widget [DEFAULT_TITLE]')

    parser.add_argument('--subscribe', '-sub', type=validate_shape_letters, default="S",
                        help=f'simple subscriber to any of Circle, Square, Triangle [S]')
    parser.add_argument('--square-history-depth', '-shd', type=int,
                        help=f'history depth for square topic [{DEFAULT_HISTORY}]')

    parser.add_argument('--publish', '-pub', type=validate_shape_letters,
                        help=f'simple publisher of any of Circle, Square, Triangle [S]')
    
    ## internal args used whilst developing/debugging only
    parser.add_argument('--justdds', '-j', type=int,
                        help='just call dds draw this many times, no graphing, for testing')
    parser.add_argument('--nap', '-n', type=float, default=0,
                        help=f'intrasample naptime [default:0.0]')

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
