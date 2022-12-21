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
from abc import ABC, abstractmethod
import logging
import os
from collections import Counter
# Connext imports
import rti.connextdds as dds
#from Shape import Shape
from ShapeTypeExtended import ShapeType, ShapeTypeExtended
from MatplotlibWrapper import MatplotlibWrapper

LOG = logging.getLogger(__name__)

def get_cwd(file):
    """@return fullpath of local file"""
    return os.path.dirname(os.path.realpath(file))

class Connext(ABC):
    """Parent class for ConnextPublisher an ConnextSubscriber"""
    WIDE_EDGE_LINE_WIDTH, THIN_EDGE_LINE_WIDTH = 2, 1
    GONE = 'gone'

    def __init__(self, args):
        self.args = args
        self.axes = None
        self.fig = None
        self.poly_dic = {}  # all polygon instances keyed by Topic+Color+InstanceNum
        self.participant = dds.DomainParticipant(args.domain_id)
        self.qos_provider = self.get_qos_provider()
        self.participant_qos = dds.QosProvider.default.participant_qos_from_profile(
                        "ShapeTypeExtended_Library::ShapeTypeExtended_Profile")
        self.participant_with_qos = dds.DomainParticipant(args.domain_id, self.participant_qos)
        #
        # participant_qos = dds.QosProvider.default.participant_qos_from_profile(
            #f'{args.qos_lib}::{args.qos_profile}')
        #type_name = "ShapeTypeExtended" if args.extended else "ShapeType"
        type_name = "ShapeTypeExtended"
        provider_type = self.qos_provider.type(type_name)
        self.topic_dic = {
            'C': dds.DynamicData.Topic(self.participant, "Circle", provider_type),
            'S': dds.DynamicData.Topic(self.participant, "Square", provider_type),
            'T': dds.DynamicData.Topic(self.participant, "Triangle", provider_type)
        }
        if args.extended:
            self.stopic_dic = {
                'C': dds.Topic(self.participant_with_qos, "Circle", ShapeTypeExtended),
                'S': dds.Topic(self.participant_with_qos, "Square", ShapeTypeExtended),
                'T': dds.Topic(self.participant_with_qos, "Triangle", ShapeTypeExtended)
            }
        else:
            self.stopic_dic = {
                'C': dds.Topic(self.participant_with_qos, "Circle", ShapeType),
                'S': dds.Topic(self.participant_with_qos, "Square", ShapeType),
                'T': dds.Topic(self.participant_with_qos, "Triangle", ShapeType)
            }
        self.sample_counter = Counter()

    def start(self, fig, axes):
        """save the matplotlib params"""
        self.fig = fig
        self.axes = axes

    @staticmethod
    def form_poly_key(which, color, instance_num=None):
        """@return a key to a polygon; must have instance number to draw (subscriber) history"""
        return f'{which}-{color}' + (f'-{instance_num}' if instance_num else "")

    @staticmethod
    def crack_poly_key(poly_key):
        """@return 3 parts of a poly_key: which, color, instance_num"""
        LOG.info(f'{poly_key=}')
        result = poly_key.split('-')
        return result if len(result) == 3 else result + [None]

    def get_qos_provider(self):
        """fetch the qos_profile from the lib in the file"""
        cwd = get_cwd(__file__)
        qos_file = self.args.qos_file
        #  prepend with cwd if starts with dot
        qos_file = cwd + qos_file[1:] if qos_file[0] == '.' else qos_file
        return dds.QosProvider(qos_file, f'{self.args.qos_lib}::{self.args.qos_profile}')

    @staticmethod
    def _get_size_and_center(points):
        if len(points) == 5:
            min_x, min_y = 0, 0
            max_x, max_y = 500, 500
            for point in points[0:4]:
                x, y = point
                min_x = x if x < min_x else min_x
                min_y = y if y < min_y else min_y
                max_x = x if x > max_x else max_x
                max_y = y if y > max_y else max_y
            size = int(max_x - min_x)
            return size, (size / 2) + min_x, int((max_y - min_y) / 2) + min_y

    def _mark2(self, which, edge_color, poly_key, char, clear=False):
        poly = self.poly_dic[poly_key]
        size, x, y = self._get_size_and_center(poly.get_xy())
        #Shape.compute_face_and_edge_color_code(color)
        fontsize = (size if char == "?" else size*2)
        if which == 'T':
            fontsize = int(fontsize * 0.7)
            y -= size * 0.45
        #weight = 'bold' if char == "?" else 'normal'
        self.poly_dic[poly_key+self.GONE+char] = self.axes.text(
            x, y, " " if clear else char, ha='center', va='center',
            color=edge_color, fontsize=fontsize, zorder=Math.maxint.zorder+1
        )


    def _mark(self, shape, poly_key, char, clear=False):
        """helper to mark or unmark the state with the passed character"""
        fc, ec = shape.get_face_and_edge_color_code()
        x, y = shape.xy
        fontsize = (shape.size if char == "?" else shape.size*2)
        if shape.which == 'T':
            fontsize = int(fontsize * 0.7)
            y -= shape.size * 0.45
        #weight = 'bold' if char == "?" else 'normal'
        key = poly_key+self.GONE+char
        text_shape = self.axes.text(
            x, y, " " if clear else char, ha='center', va='center',
            color=ec, fontsize=fontsize, zorder=shape.zorder+1
        )
        return key, text_shape

    def mark_unknown(self, shape, poly_key, clear=False):
        """mark or unmark the Unknown state - a ? in center"""
        return self._mark(shape, poly_key, "?", clear)

    def mark_gone(self, shape, poly_key, clear=False):
        """mark or unmark the Gone state - a X in center"""
        LOG.info(f'{poly_key=} {self.poly_dic[poly_key].get_xy()=}')
        return self._mark(shape, poly_key, "x", clear)

    def mark_gone_with_lines_untested(self, shape, poly_key, clear=False):
        """mark or unmark the Gone state - a X in center"""
        points = shape.get_mpl_points()
        fc, ec = shape.get_face_and_edge_color_code()
        print(f'{points=}')

        l1 = MatplotlibWrapper.create_line([(50, 50), (100, 100)], color=ec, zorder=shape.zorder+10)
        self.axes.add_line(l1)
        self.poly_dic['myline'] = l1
        if shape.which == 'S':
            for index, endpoints in enumerate([(points[0], points[2]), (points[1], points[3])]):
                if index:
                    line1 = MatplotlibWrapper.create_line(endpoints, color=ec, zorder=shape.zorder+1)
                    self.axes.add_line(line1)
                    self.poly_dic[poly_key+self.GONE+str(index)] = line1
                else:
                    line2 = MatplotlibWrapper.create_line(endpoints, color='black', zorder=shape.zorder+1)
                    self.axes.add_line(line2)
                    self.poly_dic[poly_key+self.GONE+str(index)] = line2

    def is_poly_key_gone(self, poly_key):
        return self.GONE in poly_key

    @abstractmethod
    def draw(self, _):
        """require any child implements this callback to matplotlib"""
