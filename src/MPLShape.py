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


class MPLShape():
    """holds matplotlib shape attributes and helpers"""

    """map the ShapeDemo color to the matplotlib color char"""
    COLOR_MAP = {
        'BLACK': 'k', 'BLUE': 'b', 'CYAN': 'c', 'GREEN': 'g', 'MAGENTA': 'm',
        'ORANGE': '#ff7f0e', 'PURPLE': '#9932CC',  # dark orchid
        'RED': 'r', 'WHITE': 'w', 'YELLOW': 'y' 
    }
    EDGE_LINE_WIDTH = 2

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
            self.color = self.COLOR_MAP[sample_dic['color']]
            if args.extended: 
                self.angle = sample_dic.get('angle', 0)
                self.fillKind = sample_dic.get('fillKind', 0)
        else:
            self.xy = (sample.data['x'], args.graphy - sample.data['y'])
            self.size = sample.data['shapesize'] / 2
            self.color = self.COLOR_MAP[sample.data['color']]
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
            radians = self.angle * 3.14159 / 180
            points = [self.rotate(xy, radians, x, y) for xy in points]
        return points
    

    def get_face_and_edge_color(self, pub=False):
        """policy for edge color depends on face color and pub/sub"""
        fc = 'w' if self.fillKind == 1 else self.color 
        if pub or self.color == 'w':
            return 'w', 'w'

        if self.fillKind >= 2:
            # for patterns, edge_color controls the hash lines
            return 'w', self.color
        if self.fillKind == 1: # transparent
            return 'w', 'b'

        ec = 'r' if self.color == 'b' else 'b'
        LOG.info(f'{self=} {ec=} {fc=}')
        return fc, ec

    HATCH_MAP = {0:None, 1:None, 2: "--", 3: "||"}

    def create_circle_polygon(self):
        """return a CirclePolygon"""
        LOG.debug(f'{ec=} {self.EDGE_LINE_WIDTH=}')
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
        poly.set(ec=ec, fc=fc, hatch=self.HATCH_MAP[self.fillKind], lw=self.EDGE_LINE_WIDTH)
        return poly

    def __repr__(self):
        return (f'MPLShape({self.which} {self.xy} {self.size}'
                f' color={self.color} angle={self.angle} fill={self.fillKind})')


