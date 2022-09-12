#!/usr/bin/env python

###############################################################################
# (c) Copyright, Real-Time Innovations, 2019. All rights reserved.            #
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
EDGE_LINE_WIDTH = 2
PI = 3.14159
HATCH_MAP = {0:None, 1:None, 2: "--", 3: "||"}

class MPLShape():
    """holds matplotlib shape attributes and helpers"""


    def __init__(self, args, which, sample, connector_mode=False):
        """create MPL attributes from DDS attributes"""
        #TODO:  drop connector_mode once API is working
        self.which = which
        self.angle = 0
        self.fillKind = 0

        if connector_mode:
            sample_dic = sample
            self.xy = (sample_dic['x'], args.graphy - sample_dic['y'])
            self.size = sample_dic['shapesize'] / 2
            self.color = COLOR_MAP[sample_dic['color']]
            if args.extended:
                self.angle = sample_dic.get('angle', 0)
                self.fillKind = sample_dic.get('fillKind', 0)
        else:
            self.xy = (sample.data['x'], args.graphy - sample.data['y'])
            self.size = sample.data['shapesize'] / 2
            self.color = COLOR_MAP[sample.data['color']]
            if args.extended:
                self.angle = sample.data.get('angle', 0)
                self.fillKind = sample.data.get('fillKind', 0)
        LOG.debug(f'created {self=}')


    def rotate(self, xy, radians, orig_x, orig_y):
        """apply a rotation to xy around the center""" # TODO - could pass list of vertices
        x, y = xy
        ax, ay = x-orig_x, y-orig_y
        cos_rad = math.cos(radians)
        sin_rad = math.sin(radians)
        return (orig_x + cos_rad * ax + sin_rad * ay,
                orig_y - sin_rad * ax + cos_rad * ay)


    def get_points(self):
        """Given size and center, return vertices"""
        if self.which == 'C':
            return self.xy

        x, y = self.xy
        s2 = self.size / 2
        if self.which == 'T':
            points = [(x, y+s2), (x+s2, y-s2), (x-s2, y-s2)]
        elif self.which == 'S':
            points = [(x-s2, y-s2), (x-s2, y+s2), (x+s2, y+s2), (x+s2, y-s2)]
        else:
            return None

        if self.angle != 0:
            radians = self.angle * PI / 180
            points = [self.rotate(xy, radians, x, y) for xy in points]
        return points


    def get_face_and_edge_color(self, pub=False):
        """policy for edge color depends on face color and pub/sub"""
        fc = COLOR_MAP['WHITE'] if self.fillKind == 1 else self.color
        if pub or self.color == COLOR_MAP['WHITE']:
            return COLOR_MAP['WHITE'], COLOR_MAP['WHITE']

        if self.fillKind >= 2:
            # for patterns, edge_color controls the hash lines
            return COLOR_MAP['WHITE'], self.color
        if self.fillKind == 1: # transparent
            return COLOR_MAP['WHITE'], COLOR_MAP['BLUE']

        ec = COLOR_MAP['RED'] if self.color == COLOR_MAP['BLUE'] else COLOR_MAP['BLUE']
        LOG.info(f'{self=} {ec=} {fc=}')
        return fc, ec


    def create_circle_polygon(self):
        """return a CirclePolygon"""
        LOG.debug(f'{ec=} {EDGE_LINE_WIDTH=}')
        return CirclePolygon(self.xy, radius=self.size/2)

    def create_circle(self):
        """return a circle """
        return Circle(self.xy, radius=self.size/2)

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
            LOG.info(f'SQUARE {self=}')
            poly = self.create_square()
        elif self.which == 'C':
            poly = self.create_circle()
        elif self.which == 'CP':
            poly = self.create_circle_polygon()
        else:
            LOG.error(f"unknown shape type {self=}")
            return None
        fc, ec = self.get_face_and_edge_color()
        poly.set(ec=ec, fc=fc, hatch=HATCH_MAP[self.fillKind], lw=EDGE_LINE_WIDTH)
        return poly

    def __repr__(self):
        return (f'MPLShape({self.which} {self.xy} {self.size}'
                f' color={self.color} angle={self.angle} fill={self.fillKind})')


