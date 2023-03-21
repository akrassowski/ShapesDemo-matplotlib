#!/usr/bin/env python
"""Implements shape class - holds Shape attributes"""

# python imports
import logging
import math
from typing import List, Optional, Tuple, Union

# application imports
from matplotlib.patches import Polygon
from Matplotlib import Matplotlib, ZORDER_BASE
from ShapeTypeExtended import ShapeTypeExtended
ZORDER_INC = 2  # allow room for gone line
###############################################################################
# (c) Copyright, Real-Time Innovations, 2021. All rights reserved.            #
# No duplications, whole or partial, manual or electronic, may be made        #
# without express written permission.  Any such copies, or revisions thereof, #
# must display this notice unaltered.                                         #
# This code contains trade secrets of Real-Time Innovations, Inc.             #
###############################################################################

"""Interface to App for all things shapey
   Shape is responsible for:
     ShapeDemo attributes: color, (x, y), size, fill, angle
     matplotlib env - fig, axes, patches_list
     publisher - delta_xy, delta_angle
     subscriber - pub_handle
     NOT responsible for the history-depth refs, see ConnextSubscriber for that
"""

# Constants outside Object since there's a new MPLShape for each update
PI = 3.14159
LOG = logging.getLogger(__name__)

# map the ShapeDemo color to the matplotlib color RGB code
COLOR_MAP = {
    'BLACK': 'k', 'WHITE': 'w', 'GREY': '#bebebe', 'GREYx': 'grey',
    'PURPLE': '#c03bff', 'BLUE': '#0632ff', 'RED': '#ff2600', 'GREEN': '#00fa00',
    'YELLOW': '#fffb00', 'CYAN': '#00fdff', 'MAGENTA': '#ff41ff', 'ORANGE': '#ff9500'
}
HATCH_MAP = {0: None, 1: None, 2: "--", 3: "||"}

# pylint: disable=too-many-instance-attributes
class Shape():
    """holds shape attributes and helpers"""
    shared_zorder = ZORDER_BASE  # keep zorder at Shape-level and for each instance
    limit_xy, matplotlib, poly_create_func_dic = None, None, None
    init_once = False

    # pylint: disable=too-many-arguments
    def __init__(self, matplotlib: Matplotlib, seq: int, which: str,
            color: str, xy: Tuple[int, int], size: int, pub: Optional[bool]=False,
            angle: Optional[float]=None, fill: Optional[int]=None) -> None:
        """generic constructor"""
        assert which in 'CST', f'shape must be one of CST not {which}'
        self.zorder = self.shared_zorder + ZORDER_INC
        self._gone = False
        if not self.init_once:
            self.matplotlib = matplotlib
            self.limit_xy = int(matplotlib.axes.get_xlim()[1]), int(matplotlib.axes.get_ylim()[1])
            self.poly_create_func_dic = {
                'C': self.create_circle, 'S': self.create_square, 'T': self.create_triangle
            }
        self.seq = seq
        self.color, self.which = color, which
        # now init the Shape params
        self.color_code = COLOR_MAP[color]
        self.xy = xy[0], self.limit_xy[1] - xy[1]
        #self.xy = xy[0], self.matplotlib.flip_y(xy[1])  # use flip consistently? breaks tests
        self.size = int(round(size / 2))  ## RTI ShapesDemo: top-to-bottom, MPL: radius
        self.angle, self.fill = angle, fill
        self.pub = pub
        LOG.info('created self=%s', self)

    # pylint: disable=too-many-arguments
    @classmethod
    def from_sub_sample(cls, matplotlib: Matplotlib, seq: int, which: str,
                        data: ShapeTypeExtended, extended: bool):
        """create flattened Shape attributes from DDS attributes"""
        return cls(
            matplotlib=matplotlib, seq=seq,
            which=which,
            color=data.color,
            xy=(data.x, data.y),
            size=data.shapesize,
            angle=data.angle if extended else None,
            fill=int(data.fillKind) if extended else None
        )

    @classmethod
    def from_pub_sample(cls, matplotlib: Matplotlib, which: str,
                        sample: ShapeTypeExtended, extended: bool):
        """create from a publisher sample"""
        return cls(
            matplotlib=matplotlib, seq=42,
            which=which,
            color=sample.color,
            xy=(sample.x, sample.y),
            size=sample.shapesize,
            pub=True,
            angle=sample.angle if extended else None,
            fill=sample.fillKind if extended else None
        )

    @property
    def gone(self):
        """getter for gone status"""
        return self._gone

    @gone.setter
    def gone(self, value):
        """setter for gone status"""
        self._gone = value

    def update(self, x: int, y: int, angle: Optional[float]=None):
        """change position of existing shape"""
        # ignores size/fill changes unlike Pro's ShapeDemo
        self.xy = x, self.limit_xy[1] - y
        if angle is not None:
            self.angle = angle
        Shape.shared_zorder += ZORDER_INC
        self.zorder = self.shared_zorder
        LOG.debug('zorder:%d', self.zorder)
        self.gone = False

    def get_sequence_number(self) -> int:
        """getter for sequence number"""
        return self.seq
    
    def reverse_if_wall(self, delta_xy: List[int]) -> Tuple[List[int], List[int]]:
        """helper to compute new xy coordinate and delta"""
        new_pos = [self.xy[ix] + delta_xy[ix] for ix in range(2)]
        for ix in range(2):
            if new_pos[ix] + self.size > self.limit_xy[ix]:
                delta_xy[ix] = -delta_xy[ix]
                new_pos[ix] = self.limit_xy[ix] - self.size
            elif new_pos[ix] - self.size < 0:
                delta_xy[ix] = -delta_xy[ix]
                new_pos[ix] = self.size
        return new_pos, delta_xy

    @staticmethod
    def set_poly_center(poly: Polygon, which: str, xy: List[int]) -> Polygon:
        """helper to set the poly's centerpoint"""
        assert which in 'CST', f'Invalid shape: {which}'
        if which == 'C':
            poly.set(center=xy)
        elif which in 'ST':
            poly.set_xy(xy)
        return poly

    def _rotate(self, points: List[Tuple[int, int]], radians: float) -> List[Tuple[int, int]]:
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

    def get_points(self) -> Union[Tuple[int, int], List[Tuple[int, int]]]:
        """Given size and center, return vertices"""

        if self.which == 'C':
            return self.xy

        assert self.which in 'ST', f'Shape type {self.which} not one of: CST'
        bot_y = self.xy[1] - self.size
        top_y = self.xy[1] + self.size
        bot_right = self.xy[0] + self.size, bot_y
        bot_left = self.xy[0] - self.size, bot_y
        if self.which == 'T':
            points = [
                (self.xy[0], top_y),
                bot_right,
                bot_left
            ]
        else:  # square
            points = [
                bot_left,
                (self.xy[0] - self.size, top_y),
                (self.xy[0] + self.size, top_y),
                bot_right
            ]

        if self.angle is not None:
            #LOG.info(f'ROTATING: {self.angle=}')
            points = self._rotate(points, self.angle * PI / 180)
        return points

    def face_and_edge_color_code(self):
        """compte the edge and face color from the fill and color"""
        #  matplotlib will set hatch to black if edge is set to black, so we cannot match Java Shapes
        if self.fill:
            fcolor = COLOR_MAP['WHITE']
            ecolor = COLOR_MAP[self.color]
        else:
            fcolor = COLOR_MAP[self.color]
            ecolor = COLOR_MAP['RED'] if self.color == 'BLUE' else COLOR_MAP['BLUE']
            if self.pub:
                ecolor = COLOR_MAP['BLACK']
        return fcolor, ecolor

    def create_circle(self):
        """return a circle """
        return self.matplotlib.create_circle(self.xy, radius=self.size)

    def create_square(self):
        """return a square, avoid Rectangle whose coords are diff from Triangle"""
        return self.matplotlib.create_square(self.get_points())

    def create_triangle(self):
        """return a triangle from the Polygon"""
        return self.matplotlib.create_triangle(self.get_points())

    def create_poly(self):
        """create a matplot polygon"""
        poly = self.poly_create_func_dic[self.which]()
        fcolor, ecolor = self.face_and_edge_color_code()
        hatch = HATCH_MAP[0] if self.fill is None else HATCH_MAP[self.fill]

        # LOG.info('ecolor:%s fcolor:%s zorder:%s' % (ecolor, fcolor, self.zorder))
        poly.set(ec=ecolor, fc=fcolor, hatch=hatch, zorder=self.zorder+1)
        return poly

    def __repr__(self):
        text = ('Shape:<'
                f'{self.which} seq:{self.seq} {self.xy} {self._gone} '
                f'{self.size} {self.color} Z:{self.zorder}')
        if self.pub:
            text += ' pub'
        if self.fill:
            text += f' fill:{self.fill}'
        if self.angle:
            text += f' angle:{self.angle}'
        return f'{text}> '
