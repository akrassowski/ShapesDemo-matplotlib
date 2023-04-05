#!/usr/bin/env python

###############################################################################
# (c) Copyright, Real-Time Innovations, 2021. All rights reserved.            #
# No duplications, whole or partial, manual or electronic, may be made        #
# without express written permission.  Any such copies, or revisions thereof, #
# must display this notice unaltered.                                         #
# This code contains trade secrets of Real-Time Innovations, Inc.             #
###############################################################################

"""Wrapper class for the graphing matplotlib"""

# python imports
import logging
import os

LOG = logging.getLogger(__name__)

try:
# animation imports
    import matplotlib
# TODO - use Qt5 if not on PC
    if os.name != 'nt':
        matplotlib.use('Qt5Agg')  # must precede pyplot
    import matplotlib.pyplot as plt
    from matplotlib.animation import FuncAnimation
    from matplotlib.offsetbox import OffsetImage, AnnotationBbox
    from matplotlib.patches import Circle, Polygon, Rectangle
except ImportError as exc:
    LOG.fatal("No matplotlib %s", exc)

# space between panels
ZORDER_BASE, HGAP, VGAP = 10, 35, 85


class Matplotlib:
    """Wrapper to create a graphing environment using the matplotlib library"""
    WIDE_EDGE_LINE_WIDTH, THIN_EDGE_LINE_WIDTH = 2, 1

    def __init__(self, args, image_filename=None):
        """init the figure attributes - some is Mac-specific, some must be done b4 creating fig"""
        # taken from https://stackoverflow.com/questions/
        #     7449585/how-do-you-set-the-absolute-position-of-figure-windows-with-matplotlib

        # turn off toolbar - do this FIRST
        matplotlib.rcParams['toolbar'] = 'None'
        self.plt = plt
        # create the Figure - SECOND
        #self.fig, self.axes = self.plt.subplots(figsize=args.figure_xy, num=args.box_title)
        self.fig, self.axes = self.plt.subplots(num=args.box_title)
        self.fig.set_figwidth(args.figure_xy[0])
        self.fig.set_figheight(args.figure_xy[1])
        self.axes.set_xlim((0, args.graph_xy[0]))
        self.axes.set_ylim((0, args.graph_xy[1]))

        # add a requested subtitle
        if args.subtitle:
            # font_props = {'backgroundcolor': 'w'}
            # text = self.fig.suptitle(args.subtitle, fontproperties=font_props)
            self.fig.suptitle(args.subtitle, backgroundcolor='w')

        # if args.graph_text:  # TODO: list of xy and Text to place on graph in bkgnd

        # hide the axis ticks/subticks/labels
        self.axes.use_sticky_edges = False
        if args.ticks:
            self.fig.set_figwidth(args.figure_xy[0]*1.3)
        else:
            self.axes.get_xaxis().set_visible(False)
            self.axes.get_yaxis().set_visible(False)
            # remove margin
            plt.subplots_adjust(left=0, bottom=0, right=1, top=1, wspace=0, hspace=0)

        self.init_set_position(args.position)
        self.init_show_image(image_filename)

    def init_set_position(self, position):
        """set the position of the canvas on the screen"""

        def generic_set_position(figure, x, y):
            """straddle different backends"""
            backend = matplotlib.get_backend()
            if backend == 'TkAgg':
                figure.canvas.manager.window.wm_geometry(f"+{x}+{y}")
            elif backend == 'WXAgg':
                figure.canvas.manager.window.SetPosition((x, y))
            else:
                # This works for QT and GTK
                # You can also use window.setGeometry
                figure.canvas.manager.window.move(x, y)

        # x, y, dx, dy = mngr.window.geometry().getRect()
        # Mac yields: 0, 0, 237, 272 ShapesDemo.DEFAULTS
        x, y, dx, dy = 0, 0, 237, 272
        LOG.info('x: %d y: %d dx: %d dy: %d', x, y, dx, dy)

        if isinstance(position, int):  # when passed int, treat it as slot index
            # Compute the Slots when running multiple instances
            row, row2 = VGAP+dy, 2*(dy + VGAP) -30
            cols = [(ix * dx) + HGAP for ix in range(1,5)]
            # allow for up to 15 slots by index

            coord = [(0, 0), (cols[0], 0), (cols[1], 0), (cols[2], 0), (cols[3], 0),
                    (0, row), (cols[0], row), (cols[1], row), (cols[2], row), (cols[3], row),
                    (0, row2), (cols[0], row2), (cols[1], row2), (cols[2], row2), (cols[3], row2)]
            x, y = coord[position-1]
            LOG.debug('x:%d y:%d', x, y)
        elif isinstance(position, (list, tuple)):  # when passed pair, treat as x,y
            if len(position) != 2:
                raise ValueError(f'Position parameter must be of length 2, not {position}')
            x, y = position
        else:
            raise ValueError(f'Position parameter must be int or x,y coord not {position}')
        generic_set_position(self.fig, x, y)
        #mngr.window.setGeometry(x, y, int(dx), int(dy))

    def init_show_image(self, image_filename):
        """set a background image, if provided; imagebox is used to scale when resizing"""
        if image_filename:
            image = plt.imread(image_filename)
            imagebox = OffsetImage(image, zoom=0.3, alpha=0.15)
            imagebox.image.axes = self.axes
            abox = AnnotationBbox(imagebox, (0.5, 0.5),
                                  xycoords='axes fraction', bboxprops={'lw':0})
            self.axes.add_artist(abox)

    def flip_y(self, y):
        """flip y coordinate to swich from SD to MPL"""
        return int(self.axes.get_ylim()[1] - y)

    def create_circle(self, center_xy, radius):
        """return a circle """
        return Circle(center_xy, radius)

    def create_square(self, points):
        """return a square, avoid Rectangle whose coords are diff from Triangle"""
        return Polygon(points, 4)

    def create_triangle(self, points):
        """return a triangle from the Polygon"""
        return Polygon(points, 3)

    @staticmethod
    def create_rectangle(anchor, extents, colors, zorder=ZORDER_BASE):
        """return a rectangle from extents (height, width) and colors (edge, face)"""
        poly = Rectangle(xy=anchor, height=extents[0], width=extents[1])
        poly.set(ec=colors[0], fc=colors[1], zorder=zorder)
        return poly

    @staticmethod
    def create_line(endpoints, color, zorder):
        """@return a Poly line from the pair of endpoints"""
        # dont use Line2d which is an Artist and cannot be added to poly
        line = Polygon(endpoints, closed=None, fill=None, color=color, zorder=zorder, lw=1)
        return line

    @staticmethod
    def get_points(poly):
        """return the coordinates of the vertices"""
        return poly.get_xy()

    @staticmethod
    def func_animation(fig, callback, interval, blit):
        """passthru wrapper"""
        return FuncAnimation(fig=fig, func=callback, interval=interval, blit=blit)
