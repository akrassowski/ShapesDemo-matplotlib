#!/usr/bin/env python

###############################################################################
# (c) Copyright, Real-Time Innovations, 2021. All rights reserved.            #
# No duplications, whole or partial, manual or electronic, may be made        #
# without express written permission.  Any such copies, or revisions thereof, #
# must display this notice unaltered.                                         #
# This code contains trade secrets of Real-Time Innovations, Inc.             #
###############################################################################

"""Implements multiplotlib shape class (MPLShape)"""
"""Interface to App for all things shapey
   Shape -> 
     color, (x, y), size, fill, angle
     polygon_list (self, gone)
     plot - axes, patches_list
     publisher - delta_xy, delta_angle
     subscriber - history sibling refs
"""

# python imports
import logging
import math

# animation imports
from matplotlib.patches import Circle, Polygon

#from ShapeTypeExtended import ShapeType, ShapeTypeExtended


# Constants outside Object since there's a new MPLShape for each update
PI = 3.14159
ZORDER_INC = 1
LOG = logging.getLogger(__name__)

# map the ShapeDemo color to the matplotlib color RGB code
COLOR_MAP = {
    'BLACK': 'k', 'WHITE': 'w',
    'PURPLE': '#c03bff', 'BLUE': '#0632ff', 'RED': '#ff2600', 'GREEN': '#00fa00',
    'YELLOW': '#fffb00', 'CYAN': '#00fdff', 'MAGENTA': '#ff41ff', 'ORANGE': '#ff9500'
}
HATCH_MAP = {0: None, 1: None, 2: "--", 3: "||"}

class Shape():
    """holds shape attributes and helpers"""
    shared_zorder = 10

    def __init__(self, seq, which, limit_xy, color, xy, size, angle=None, fill=None):
        """generic constructor"""
        self.seq = seq
        self.which = which
        if which not in 'CST':
            raise ValueError(f'shape must be one of CST not {which}')
        self.limit_xy = limit_xy
        self.color = color
        self.zorder = ZORDER_INC
        self.poly_create_func = {
            'C': self.create_circle,
            'S': self.create_square,
            'T': self.create_triangle
        }
        # now init the MPL Shape params
        self.color_code = COLOR_MAP[self.color]
        self.xy = xy[0], limit_xy[1] - xy[1]
        self.size = int(round(size / 2))  ## RTI ShapesDemo: top-to-bottom, MPL: radius
        self.angle = angle
        self.fill = fill
        LOG.info('created self=%s', self)

    @classmethod
    def from_sub_sample_seq(cls, seq, which, limit_xy, data, extended):
        """create flattened Shape attributes from DDS attributes"""
        return cls(
            seq=seq,
            which=which,
            limit_xy=limit_xy,
            color=data.color,
            xy=(data.x, data.y),
            size=data.shapesize,
            angle=data.angle if extended else 0,
            fill=int(data.fillKind) if extended else 0
        )

    @classmethod
    def from_pub_sample(cls, which, limit_xy, sample, extended):
        """create from a publisher sample"""
        return cls(
            seq=42,
            which=which,
            limit_xy=limit_xy,
            color=sample.color,
            xy=(sample.x, sample.y),
            size=sample.shapesize,
            angle=sample.angle if extended else 0,
            fill=sample.fillKind if extended else 0
        )

    def update(self, x, y, angle=None):
        """change position of existing shape"""
        # ignores size/fill changes
        self.xy = x, self.limit_xy[1] - y
        if angle is not None:
            self.angle = angle

    def mpl2sd(self, center_y):
        """@return the supplied MPL Y value converted to ShapeDemo pixels"""
        return self.limit_xy[1] - center_y

    def get_sequence_number(self):
        """getter for sequence number"""
        return self.seq

    def reverse_if_wall(self, delta_xy):
        """helper to compute new xy coordinate and delta"""
        new_pos = [ self.xy[ix] + delta_xy[ix] for ix in range(2)]
        for ix in range(2):
            if new_pos[ix] + self.size > self.limit_xy[ix]:
                delta_xy[ix] = -delta_xy[ix]
                new_pos[ix] = self.limit_xy[ix] - self.size
            elif new_pos[ix] - self.size < 0:
                delta_xy[ix] = -delta_xy[ix]
                new_pos[ix] = self.size
        return new_pos, delta_xy

    @staticmethod
    def set_poly_center(poly, which, xy):
        """helper to set the poly's centerpoint"""
        if which == 'C':
            poly.set(center=xy)
        elif which in 'ST':
            poly.set_xy(xy)
        else:
            raise ValueError(f'Invalid shape: {which}')
        return poly

    def _rotate(self, points, radians):
        """apply a rotation around the center"""
        ret_val = []
        center_x, center_y = self.xy
        cos_rad = math.cos(radians)
        sin_rad = math.sin(radians)
        for point in points:
            adj_x, adj_y = point[0] - center_x, point[1] - center_y
            ret_val.append(
                (round(center_x + (cos_rad * adj_x) + (sin_rad * adj_y)),
                 round(center_y - (sin_rad * adj_x) + (cos_rad * adj_y)))
            )
        return ret_val

    def get_mpl_points(self):
        """@Return the adjusted points for use by matplotlib"""
        if self.which == 'C':
            return self.xy[0], self.mpl2sd(self.xy[1])

        center_x, center_y = self.xy
        size = self.size
        if self.which == 'S':
            points = [
                (center_x - size, self.mpl2sd(center_y - size)),
                (center_x - size, self.mpl2sd(center_y + size)),
                (center_x + size, self.mpl2sd(center_y + size)),
                (center_x + size, self.mpl2sd(center_y - size))
            ]
        return points

    def get_points(self):
        """Given size and center, return vertices; also move to top with zorder"""
        #LOG.debug('angle:%d', self.angle)
        Shape.shared_zorder += ZORDER_INC
        self.zorder = self.shared_zorder
        LOG.debug('zorder:%d', self.zorder)
        if self.which == 'C':
            return self.xy

        center_x, center_y = self.xy
        size = self.size
        if self.which == 'T':
            points = [
                (center_x, center_y + size),
                (center_x + size, center_y - size),
                (center_x - size, center_y - size)
            ]
        elif self.which == 'S':
            points = [
                (center_x - size, center_y - size),
                (center_x - size, center_y + size),
                (center_x + size, center_y + size),
                (center_x + size, center_y - size)
            ]
        else:
            raise ValueError(f'Shape type {self.which} not one of: CST')

        if self.angle:
            #LOG.info(f'ROTATING: {self.angle=}')
            points = self._rotate(points, self.angle * PI / 180)
        return points

    @staticmethod
    def compute_face_and_edge_color_code(fill, color):
        if fill == 0 or fill is None:
            fcolor = COLOR_MAP[color] 
            ecolor = COLOR_MAP['RED'] if color == 'BLUE' else COLOR_MAP['BLUE']
        elif fill >= 2:
            # for patterns, edge_color controls the hash lines
            fcolor, ecolor = COLOR_MAP['WHITE'], COLOR_MAP[color]
        else:
            fcolor, ecolor = COLOR_MAP['WHITE'], COLOR_MAP['BLUE']
        return fcolor, ecolor

    def get_face_and_edge_color_code(self):
        """policy for edge color depends on face color"""
        fcolor, ecolor = self.compute_face_and_edge_color_code(self.fill, self.color)
        LOG.debug('self=%s ecolor=%s fcolor=%s', self, ecolor, fcolor)
        return fcolor, ecolor

    def get_face_and_edge_color_ori(self):
        """policy for edge color depends on face color"""
        if self.fill == 0:
            fcolor = self.color_code
            ecolor = COLOR_MAP['RED'] if self.color == 'BLUE' else COLOR_MAP['BLUE']
        elif self.fill >= 2:
            # for patterns, edge_color controls the hash lines
            fcolor, ecolor = COLOR_MAP['WHITE'], self.color_code
        else:  # transparent
            fcolor, ecolor = COLOR_MAP['WHITE'], COLOR_MAP['BLUE']
        LOG.debug('self=%s ecolor=%s fcolor=%s', self, ecolor, fcolor)
        return fcolor, ecolor

    def create_circle(self):
        """return a circle """
        return Circle(self.xy, radius=self.size)

    def create_square(self):
        """return a square, avoid Rectangle whose coords are diff from Triangle"""
        return Polygon(self.get_points(), 4)

    def create_triangle(self):
        """return a triangle from the Polygon"""
        return Polygon(self.get_points(), 3)

    def create_poly(self):
        """create a matplot polygon"""
        poly = self.poly_create_func[self.which]()
        fcolor, ecolor = self.get_face_and_edge_color_code()
        poly.set(ec=ecolor, fc=fcolor,
                 hatch=HATCH_MAP[self.fill], zorder=self.zorder)
        return poly

    def __repr__(self):
        text = ('Shape:<'
                f'{self.which} seq:{self.seq} {self.xy} '
                f'{self.size} {self.color} Z:{self.zorder}')
        if self.fill:
            text += f' fill:{self.fill}'
        if self.angle:
            text += f' angle:{self.angle}'
        return f'{text}> '
