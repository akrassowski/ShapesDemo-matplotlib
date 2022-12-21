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
    from matplotlib.lines import Line2D
except ImportError as exc:
    LOG.fatal("No matplotlib %s", exc)

# space between panels
HORIZONTAL_GAP, VERTICAL_GAP = 30, 85

class MatplotlibWrapper:
    """Wrapper to create a graphing environment using the matplotlib library"""

    @staticmethod
    def create_matplot(figure_xy, graph_xy, image_filename, box_title="", index=0, subtitle=None):
        """init the figure attributes - some is Mac-specific, some must be done b4 creating fig"""
        # taken from https://stackoverflow.com/questions/
        #     7449585/how-do-you-set-the-absolute-position-of-figure-windows-with-matplotlib

        # turn off toolbar - do this FIRST
        matplotlib.rcParams['toolbar'] = 'None'

        # create the Figure - SECOND
        fig, axes = plt.subplots(figsize=figure_xy, num=box_title)
        axes.set_xlim((0, graph_xy[0]))
        axes.set_ylim((0, graph_xy[1]))

        # add a requested subtitle
        if subtitle:
            fig.suptitle(subtitle)

        # hide the axis ticks/subticks/labels
        axes.get_xaxis().set_visible(False)
        axes.get_yaxis().set_visible(False)

        # remove margin
        plt.subplots_adjust(left=0, bottom=0, right=1, top=1, wspace=0, hspace=0)

        # Compute the Slots when running multiple instances
        # get the x, y, dx, dy
        mngr = plt.get_current_fig_manager()
        x, y, dx, dy = mngr.window.geometry().getRect()
        row, row2, space_x = VERTICAL_GAP + dy, VERTICAL_GAP + 2*dy, HORIZONTAL_GAP+5
        cols = [dx+HORIZONTAL_GAP, 2*dx+space_x, 3*dx+space_x, 4*dx+space_x]
        # allow for up to 15 slots by index
        coord = [(0, 0), (cols[0], 0), (cols[1], 0), (cols[2], 0), (cols[3], 0),
                 (0, row), (cols[0], row), (cols[1], row), (cols[2], row), (cols[3], row),
                 (0, row2), (cols[0], row2), (cols[1], row2), (cols[2], row2), (cols[3], row2)]
        x, y = coord[index-1]
        LOG.debug('x=%d, y=%d', x, y)
        mngr.window.setGeometry(x, y, int(dx), int(dy))

        # set a background image  # TODO scale when resizing via on_click canvas events
        image = plt.imread(image_filename)
        fig.figimage(image, xo=35, yo=120, zorder=3, alpha=0.1)

        return fig, axes, plt

    @staticmethod
    def create_line(endpoints, color, zorder):
        """@return a 2d line from the pair of endpoints"""
        line = Line2D(endpoints[0], endpoints[1], color=color, zorder=zorder, lw=2)
        return line

    @staticmethod
    def func_animation(fig, callback, interval, blit):
        """passthru wrapper"""
        return FuncAnimation(fig=fig, func=callback, interval=interval, blit=blit)
