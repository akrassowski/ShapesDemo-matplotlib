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
import logging
import os
import sys
import time

# Connext imports
import rti.connextdds as dds
# It is required that the rtiddsgen be alreay run to create the type class
# The generated <datatype>.py class file should be included here
from ShapeTypeExtended import ShapeType, ShapeTypeExtended

from Connext import Connext
from Shape import Shape
from InstanceGen import InstanceGen
from ShapeTypeExtended import ShapeTypeExtended

LOG = logging.getLogger(__name__)


class ConnextPub(Connext):

    def __init__(self, args, config=None):
        super().__init__(args)
        self.args = args
        self.publisher = dds.Publisher(self.participant)
        writer_qos = self.qos_provider.datawriter_qos
        self.writer_dic = {}
        self.sample_dic = {}
        for which in 'S':  ## TODO for now
            LOG.info(f'{self.topic_dic=} \n{self.participant=}')
            #self.writer_dic[which] = dds.DataWriter(self.participant.implicit_publisher, self.topic_dic[which])
            self.writer_dic[which] = dds.DataWriter(self.publisher, self.topic_dic[which])
        self.pub_dic = config
        LOG.info(self.pub_dic)


    def start(self, fig, axes):
        """First, some globals and helpers"""
        self.fig = fig
        self.axes = axes

        participant = dds.DomainParticipant(self.args.domain_id)
        #for publisher in self.pub_dic.keys():
            #publisher_dic = config_dic[publisher]
        for which in self.pub_dic.keys():
            self.publish_sample(which)

    def create_default_sample(self, which):
        sample.x, sample.y = 50, 50
        sample.color = 'BLUE'
        sample.shapesize = 30
        return sample

    def publish_sample(self, which):
        self.sample_counter.update(f'{which}w')
        sample = self.sample_dic.get(which)
        attrib_dic = self.pub_dic[shape]
        LOG.info(attrib_dic)
      
        if sample:
            sample.x += 10 
            if sample.x > 240:
                sample.x = 0
            sample.y += 10
            if sample.y > 240:
                sample.y = 0
        else:
            sample = self.creat_default_sample(which)
        writer_dic[which].write(sample)
        sample_dic[which] = sample


    def fetch_and_draw(self, ignoreMe):
        writers = self.writer_dic.values()
        whiches = self.writer_dic.keys()
        for writer, which in zip(writers, whiches):
            self.publish_sample(writer, which)

        return self.poly_dic.values()
