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
from Connext import get_cwd

LOG = logging.getLogger(__name__)

try:
# animation imports
    import matplotlib
# TODO - use Qt5 if not on PC
    if os.name != 'nt':
        matplotlib.use('Qt5Agg')  # must precede pyplot
    import matplotlib.pyplot as plt
    from matplotlib.animation import FuncAnimation
except ImportError as exc:
    LOG.fatal("No matplotlib %s", exc)

# space between panels
HORIZONTAL_GAP, VERTICAL_GAP = 30, 85

class MatplotlibWrapper:
    """Wrapper to create a graphing environment using the matplotlib library"""

    @staticmethod
    def create_matplot(figure_xy, graph_xy, box_title="", index=0, subtitle=None):
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
        row_y, space_x = VERTICAL_GAP + dy, HORIZONTAL_GAP+5
        coord = [(0, 0), (dx+HORIZONTAL_GAP, 0), (2*dx+space_x, 0),
                 (0, row_y), (dx+HORIZONTAL_GAP, row_y), (2*dx+space_x, row_y)]
        x, y = coord[index-1]
        LOG.debug('x=%d, y=%d', x, y)
        mngr.window.setGeometry(x, y, int(dx), int(dy))

        # set a background image  # TODO scale when resizing via onclick canvas events
        cwd = get_cwd(__file__)
        image = plt.imread(f'{cwd}/RTI_Logo_RGB-Color.png')
        fig.figimage(image, xo=35, yo=120, zorder=3, alpha=0.1)

        return fig, axes, plt

    @staticmethod
    def func_animation(fig, callback, interval, blit):
        """passthru wrapper"""
        return FuncAnimation(fig=fig, func=callback, interval=interval, blit=blit)
