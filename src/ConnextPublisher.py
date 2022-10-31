#!/usr/bin/env python

###############################################################################
# (c) Copyright, Real-Time Innovations, 2021. All rights reserved.            #
# No duplications, whole or partial, manual or electronic, may be made        #
# without express written permission.  Any such copies, or revisions thereof, #
# must display this notice unaltered.                                         #
# This code contains trade secrets of Real-Time Innovations, Inc.             #
###############################################################################

"""Publishes Shapes and displays them"""


# python imports
import logging

# Connext imports
import rti.connextdds as dds
# It is required that the rtiddsgen be alreay run to create the type class
# The generated <datatype>.py class file should be included here
from ShapeTypeExtended import ShapeTypeExtended
# from ShapeTypeExtended import ShapeType, ShapeTypeExtended

from ArgParser import ArgParser
from ConfigParser import ConfigParser
from Connext import Connext
from Shape import Shape

LOG = logging.getLogger(__name__)


class ConnextPublisher(Connext):
    """Publish only 1 shape for now"""

    def __init__(self, args, config=None):
        super().__init__(args)
        self.publisher = dds.Publisher(self.sparticipant)
        writer_qos = self.qos_provider.datawriter_qos  ## TODO: use me
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
        super().start(fig, axes)
        for which in self.pub_dic.keys():
            self.publish_sample(which)


    def create_default_sample(self, which):
        """use the defaults to create a sample"""
        LOG.debug(f'{which=}')
        sample = ShapeTypeExtended()
        defaults = self.pub_dic[which]
        sample.x, sample.y = defaults['xy']
        sample.color = defaults['color']
        sample.shapesize = defaults['shapesize']
        sample.fillKind = defaults['fillKind']
        sample.angle = defaults['angle']
        return sample


    @staticmethod
    def _inc_with_bounce(value, inc, limit):
        new_value = value + inc 
        if new_value < 0:
            inc *= -1
            new_value = 0
        elif new_value > limit:
            inc *= -1
            new_value = limit
        return new_value, inc

    def _move_shape(self, sample, which):
        """move the shape"""
        dx, dy = self.pub_dic[which]['delta_xy']
        sample.x, dx = self._inc_with_bounce(sample.x, dx, ArgParser.MAXX)
        sample.y, dy = self._inc_with_bounce(sample.y, dy, ArgParser.MAXY)
        self.pub_dic[which]['delta_xy'] = dx, dy
        LOG.debug(f'{sample=}')
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
            sample = self._move_shape(sample, which)
        else:  ## start with the default
            sample = self.create_default_sample(which)

        shape = Shape.from_pub_sample(
            which=which,
            args=self.args,
            color=sample.color,
            xy=(sample.x, sample.y),
            size=sample.shapesize,
            angle=sample.angle,
            fillKind=sample.fillKind
        )
        poly_key = self.form_poly_key(which, shape.color, 1)
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
        poly.set(lw=self.THIN_EDGE_LINE_WIDTH, zorder=shape.zorder)

        self.writer_dic[which].write(sample)  ## publish the sample
        self.sample_dic[which] = sample       ##   and remember it


    def fetch_and_draw(self, _):
        """callback for matplotlib to update shapes"""
        for which in self.writer_dic.keys():
            self.publish_sample(which)

        return self.poly_dic.values()
