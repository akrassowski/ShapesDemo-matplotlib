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
##from InstanceGen import InstanceGen
from Shape import Shape
from ShapeTypeExtended import ShapeTypeExtended

LOG = logging.getLogger(__name__)


class ConnextPub(Connext):

    def __init__(self, args, config=None):
        super().__init__(args)
        self.args = args
        self.publisher = dds.Publisher(self.sparticipant)
        writer_qos = self.qos_provider.datawriter_qos
        self.writer_dic = {}
        self.sample_dic = {}
        for which in 'CST':  ## TODO for now
            LOG.info(f'{self.stopic_dic=} \n{self.participant=}')
            #self.writer_dic[which] = dds.DataWriter(self.participant.implicit_publisher, self.stopic_dic[which])
            self.writer_dic[which] = dds.DataWriter(self.publisher, self.stopic_dic[which])
        self.pub_dic = config
        LOG.info(self.pub_dic)


    def start(self, fig, axes):
        """First, some globals and helpers"""
        self.fig = fig
        self.axes = axes

        #for publisher in self.pub_dic.keys():
            #publisher_dic = config_dic[publisher]
        for which in self.pub_dic.keys():
            self.publish_sample(which)


    def create_default_sample(self, which):
        """TODO: copy from the config"""
        sample = ShapeTypeExtended()
        sample.x, sample.y = 50, 50
        sample.color = 'BLUE'
        sample.shapesize = 30
        return sample

    @staticmethod
    def _move_shape(sample):
        """move the shape"""
        sample.x += 10 
        if sample.x > 240:
            sample.x = 0
        sample.y += 10
        if sample.y > 240:
            sample.y = 0
        LOG.info(f'{sample=}')
        return sample

    def publish_sample(self, which):
        self.sample_counter.update(f'{which}w')
        try:
            attrib_dic = self.pub_dic[which]
            LOG.debug(attrib_dic)
        except KeyError:
            return  ## no entry = nothing to do
      
        sample = self.sample_dic.get(which)
        if sample:  ## update last sample
            sample = self._move_shape(sample)
        else:  ## start with the default
            sample = self.create_default_sample(which)

        shape = Shape.from_pub_sample(which=which,
                      scolor=sample.color,
                      xy=(sample.x, sample.y),
                      size=sample.shapesize,
                      angle=sample.angle,
                      fillKind=sample.fillKind
        )
        poly_key = self.form_poly_key(which, shape.scolor, 1)
        poly = self.poly_dic.get(poly_key)
        if self.args.justdds:
            LOG.info("early exit")
            return
        if not poly:
            poly = shape.create_poly()
            self.poly_dic[poly_key] = poly
            LOG.debug(f"added {poly_key=}")
            self.axes.add_patch(poly)

        # update the plot
        xy = shape.get_points()
        poly.set_xy(xy)
        poly.set(lw=self.WIDE_EDGE_LINE_WIDTH, zorder=shape.zorder)

        self.writer_dic[which].write(sample)  ## publish the sample
        self.sample_dic[which] = sample       ##   and remember it


    def fetch_and_draw(self, ignoreMe):
        writers = self.writer_dic.values()
        whiches = self.writer_dic.keys()
        for writer, which in zip(writers, whiches):
            self.publish_sample(which)

        return self.poly_dic.values()
