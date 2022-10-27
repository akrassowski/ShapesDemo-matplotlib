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
import sys
import time
from collections import Counter
# Connext imports
import rti.connextdds as dds
from ShapeTypeExtended import ShapeTypeExtended

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.INFO)


class Connext(ABC):
    WIDE_EDGE_LINE_WIDTH, THIN_EDGE_LINE_WIDTH = 2, 1

    def __init__(self, args):
        self.args = args
        self.poly_dic = {}  # all polygon instances keyed by Topic+Color+InstanceNum
        self.participant = dds.DomainParticipant(args.domain_id)
        self.sparticipant = dds.DomainParticipant(args.domain_id)
        self.qos_provider = self.get_qos_provider()

        type_name = "ShapeTypeExtended" if args.extended else "ShapeType"
        provider_type = self.qos_provider.type(type_name)
        self.topic_dic = {
            'C': dds.DynamicData.Topic(self.participant, "Circle", provider_type),
            'S': dds.DynamicData.Topic(self.participant, "Square", provider_type),
            'T': dds.DynamicData.Topic(self.participant, "Triangle", provider_type)
        }
        self.stopic_dic = {
            'C': dds.Topic(self.sparticipant, "Circle", ShapeTypeExtended),
            'S': dds.Topic(self.sparticipant, "Square", ShapeTypeExtended),
            'T': dds.Topic(self.sparticipant, "Triangle", ShapeTypeExtended)
        }
        self.sample_counter = Counter()

    @staticmethod
    def form_poly_key(which, color, instance_num):
        return f'{which}-{color}-{instance_num}'

    @staticmethod
    def get_cwd(file):
        return os.path.dirname(os.path.realpath(file))

    def get_qos_provider(self):
        """fetch the qos_profile from the lib in the file"""
        cwd = self.get_cwd(__file__)
        qos_file = self.args.qos_file
        #  prepend with cwd if starts with dot
        qos_file = cwd + qos_file[1:] if qos_file[0] == '.' else qos_file
        return dds.QosProvider(qos_file, f'{self.args.qos_lib}::{self.args.qos_profile}')

    @abstractmethod
    def fetch_and_draw(self):
        pass