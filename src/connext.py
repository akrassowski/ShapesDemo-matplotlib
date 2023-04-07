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
from abc import ABC
from collections import Counter
import logging
from math import sqrt
import os

# Connext imports
import rti.connextdds as dds
from ShapeTypeExtended import ShapeType, ShapeTypeExtended

LOG = logging.getLogger(__name__)

def get_cwd(file):
    """@return fullpath of local file"""
    return os.path.dirname(os.path.realpath(file))

def possibly_log_qos(qos_log_level, entity):
    """log the qos at selected log level on its own"""
    if qos_log_level is not None:
        try:
            LOG.log(qos_log_level, '\n' + entity.qos.to_string())
        except AttributeError:
            LOG.log(qos_log_level, "No qos attribute \n" + entity.to_string())


class Connext(ABC):
    """Parent class for ConnextPublisher an ConnextSubscriber"""
    poly_dic = {}  # all polygon instances keyed by Topic+Color+InstanceNum and Gone
    sample_counter = Counter()
    participant_qos = dds.QosProvider.default.participant_qos_from_profile(
        "ShapeTypeExtended_Library::ShapeTypeExtended_Profile")

    def __init__(self, matplotlib, args):
        self.args = args
        self.matplotlib = matplotlib
        self.participant = dds.DomainParticipant(args.domain_id)
        possibly_log_qos(self.args.log_qos, self.participant)

        self.qos_provider = self.get_qos_provider()
        self.rw_qos_provider = dds.QosProvider(args.qos_file, f'{args.qos_lib}::{args.qos_profile}')
        entity_name = dds.EntityName('EntityNameIsFred')
        entity_name.role_name = 'the role of Fred'
        self.participant_qos.participant_name = entity_name
        possibly_log_qos(self.args.log_qos, self.participant_qos)

        self.participant_with_qos = dds.DomainParticipant(args.domain_id, self.participant_qos)
        if args.extended:
            self.topic_dic = {
                'C': dds.Topic(self.participant_with_qos, "Circle", ShapeTypeExtended),
                'S': dds.Topic(self.participant_with_qos, "Square", ShapeTypeExtended),
                'T': dds.Topic(self.participant_with_qos, "Triangle", ShapeTypeExtended)
            }
        else:
            self.topic_dic = {
                'C': dds.Topic(self.participant_with_qos, "Circle", ShapeType),
                'S': dds.Topic(self.participant_with_qos, "Square", ShapeType),
                'T': dds.Topic(self.participant_with_qos, "Triangle", ShapeType)
            }

    @staticmethod
    def form_poly_key(which, color, instance_num=None):
        """@return a key to a polygon; must have instance number to draw (subscriber) history"""
        return f'{which}-{color}' + (f'-{instance_num}' if instance_num else "")

    def get_qos_provider(self):
        """fetch the qos_profile from the lib in the file"""
        cwd = get_cwd(__file__)
        qos_file = self.args.qos_file
        #  prepend with cwd if starts with dot
        qos_file = cwd + qos_file[1:] if qos_file[0] == '.' else qos_file
        return dds.QosProvider(qos_file, f'{self.args.qos_lib}::{self.args.qos_profile}')

    # marking methods are currently only used by Subscriber; could be relocated
    @staticmethod
    def _get_center(points):
        min_x = max_x = points[0][0]
        min_y = max_y = points[0][1]
        num_points = len(points)
        if num_points in [4, 5]:  # square, triangle
            for point in points[1:]:
                x, y = point
                min_x = x if x < min_x else min_x
                min_y = y if y < min_y else min_y
                max_x = x if x > max_x else max_x
                max_y = y if y > max_y else max_y
                LOG.info(f'{min_x=} {min_y=} {max_x=} {max_y=}')
            size = int(max_x - min_x)
            return (size / 2) + min_x, int((max_y - min_y) / 2) + min_y
        raise NotImplementedError("add circle")

    def _mark(self, shape, poly_key, the_char):
        """helper to mark or unmark the state with the passed character"""
        LOG.info(f'{poly_key=} {shape=} {the_char=}')
        poly = self.poly_dic[poly_key]
        zorder = poly.zorder + 1  # ensure drawn over shape
        center = poly.center if shape.which == 'C' else self._get_center(poly.get_xy())
        if the_char.upper() == 'X':
            return self._mark_line(center, shape, poly_key, zorder)
        raise NotImplementedError(f'non-X mark: {the_char}')

    def _get_x_points(self, center, shape, poly_key):
        """helper to get the vertices of the X"""
        if shape.which == 'C':
            # top-left, bottom-right, center, top_right, bottom-left
            x, y = center
            delta = sqrt((shape.size ** 2) / 2)
            lt_x, rt_x, tp_y, bt_y = x - delta, x + delta, y + delta, y - delta
            endpoints = [[lt_x, tp_y], [rt_x, bt_y], center, [rt_x, tp_y], [lt_x, bt_y]]
        else:  # non-Circle
            poly = self.poly_dic[poly_key]
            points = self.matplotlib.get_points(poly)
            if shape.which == 'S':
                # top-left, bottom-right, center, top_right, bottom-left
                endpoints = [points[0], points[2], center, points[1], points[3]]
            elif shape.which == 'T':
                # top-center, center, bottom-left, center, bottom-right
                endpoints = [points[0], center, points[1], center, points[2]]
            else:
                raise ValueError(f'Shape must be one of: CST not {shape.which}')
        return endpoints

    def _mark_line(self, center, shape, poly_key, zorder):
        """Mark an X as a multi-step line"""

        _, edge_color = shape.face_and_edge_color_code()
        endpoints = self._get_x_points(center, shape, poly_key)
        key = f'{poly_key}-gone'
        line = self.matplotlib.create_line(endpoints, color=edge_color, zorder=zorder)
        LOG.debug(f'{key=} {endpoints=} {edge_color=} {zorder=} {line=}')
        self.matplotlib.axes.add_patch(line)
        return key, line

    def mark_unknown(self, shape, poly_key):
        """mark the Unknown state - a ? in center"""
        return self._mark(shape, poly_key, "?")

    def mark_gone(self, shape, poly_key):
        """mark the Gone state - a X in center"""
        shape.gone = True
        fstr = f'{poly_key=} {shape.xy=}'
        if shape.which != 'C':
            fstr += ' {self.poly_dic[poly_key].get_xy()=}'
        LOG.info(fstr)
        return self._mark(shape, poly_key, "x")

    #  @abstractmethod
    def draw(self, _):
        """require any child implements this callback to matplotlib"""
        raise ValueError
