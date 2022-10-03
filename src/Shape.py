#!/usr/bin/env python

###############################################################################
# (c) Copyright, Real-Time Innovations, 2021. All rights reserved.            #
# No duplications, whole or partial, manual or electronic, may be made        #
# without express written permission.  Any such copies, or revisions thereof, #
# must display this notice unaltered.                                         #
# This code contains trade secrets of Real-Time Innovations, Inc.             #
###############################################################################

"""Implements multiplotlib shape class (MPLShape)"""


# python imports
import logging
import math

# animation imports
from matplotlib.patches import Circle, Polygon, CirclePolygon

LOG = logging.getLogger(__name__)


"""Constants outside Object since there's a new MPLShape for each update"""
"""map the ShapeDemo color to the matplotlib color RGB code"""
COLOR_MAP = {
    'BLACK': 'k', 'WHITE': 'w',
    'PURPLE': '#c03bff', 'BLUE': '#0632ff', 'RED': '#ff2600', 'GREEN': '#00fa00',
    'YELLOW': '#fffb00', 'CYAN': '#00fdff', 'MAGENTA': '#ff41ff', 'ORANGE': '#ff9500'
}
PI = 3.14159
HATCH_MAP = {0: None, 1: None, 2: "--", 3: "||"}

ZORDER_INC = 1


class Shape():
    """holds shape attributes and helpers"""

    shared_zorder = 10

    def __init__(self, args, which, data, info):
        """create flattened Shape attributes from DDS attributes"""
        self.which = which
        self.seq = info.reception_sequence_number.value
        self.zorder = ZORDER_INC

        self.xy = (data['x'], args.graphy - data['y'])
        self.size = data['shapesize'] / 2
        self.scolor = data['color']  # keep sample color for debugging
        self.color = COLOR_MAP[self.scolor]
        if args.extended:
            self.angle = data['angle']
            self.fillKind = data['fillKind']
        else:
            self.angle = 0
            self.fillKind = 0
        LOG.debug(f'created {self=}')

    def get_sequence_number(self):
        return self.seq

    def rotate(self, xy, radians, orig_x, orig_y):
        """apply a rotation to xy around the center"""  # TODO - could pass list of vertices
        ax, ay = xy[0] - orig_x, xy[1] - orig_y
        cos_rad = math.cos(radians)
        sin_rad = math.sin(radians)
        return (orig_x + cos_rad * ax + sin_rad * ay,
                orig_y - sin_rad * ax + cos_rad * ay)

    def get_points(self):
        """Given size and center, return vertices; also move to top with zorder"""
        Shape.shared_zorder += ZORDER_INC
        self.zorder = self.shared_zorder
        if self.which == 'C':
            return self.xy

        x, y = self.xy
        s2 = self.size
        if self.which == 'T':
            points = [(x, y + s2), (x + s2, y - s2), (x - s2, y - s2)]
        elif self.which == 'S':
            points = [(x - s2, y - s2), (x - s2, y + s2),
                      (x + s2, y + s2), (x + s2, y - s2)]
        else:
            return None

        if self.angle:
            radians = self.angle * PI / 180
            points = [self.rotate(xy, radians, x, y) for xy in points]
        return points

    def get_face_and_edge_color(self, pub=False):
        """policy for edge color depends on face color and pub/sub"""
        if self.fillKind == 0:
            fc = self.color
            ec = COLOR_MAP['RED'] if self.color == COLOR_MAP['BLUE'] else COLOR_MAP['BLUE']
        elif self.fillKind >= 2:
            # for patterns, edge_color controls the hash lines
            fc, ec = COLOR_MAP['WHITE'], self.color
        else:  # transparent
            fc, ec = COLOR_MAP['WHITE'], COLOR_MAP['BLUE']
        LOG.debug(f'{self=} {ec=} {fc=}')
        return fc, ec

    def create_circle_polygon(self):
        """return a CirclePolygon"""
        return CirclePolygon(self.xy, radius=self.size)

    def create_circle(self):
        """return a circle """
        return Circle(self.xy, radius=self.size)

    def create_square(self):
        """return a square, avoid Rectangle whose coords are diff from Triangle"""
        return Polygon(self.get_points(), 4)

    def create_triangle(self):
        """return a triangle from the Polygon"""
        return Polygon(self.get_points(), 3)

    def create_poly(self):  # TODO:opt use funcmap from which
        """create a matplot shape from a MPL shape"""
        if self.which == 'T':
            poly = self.create_triangle()
        elif self.which == 'S':
            LOG.debug(f'SQUARE {self=}')
            poly = self.create_square()
        elif self.which == 'C':
            poly = self.create_circle()
        elif self.which == 'CP':
            poly = self.create_circle_polygon()
        else:
            LOG.error(f"unknown shape type {self=}")
            return None
        fc, ec = self.get_face_and_edge_color()
        poly.set(ec=ec, fc=fc,
                 hatch=HATCH_MAP[self.fillKind], zorder=self.zorder)
        return poly

    def __repr__(self):
        s = f'Shape:{self.which} seq:{self.seq} {self.xy} {self.size} {self.scolor} Z:{self.zorder}'
        if self.fillKind:
            s += f' fill:{self.fillKind}'
        if self.angle:
            s += f' angle:{self.angle}'
        return s
