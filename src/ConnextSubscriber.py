#!/usr/bin/env python

###############################################################################
# (c) Copyright, Real-Time Innovations, 2021. All rights reserved.            #
# No duplications, whole or partial, manual or electronic, may be made        #
# without express written permission.  Any such copies, or revisions thereof, #
# must display this notice unaltered.                                         #
# This code contains trade secrets of Real-Time Innovations, Inc.             #
###############################################################################

"""Subscribes to Shapes and updates them in matplotlib"""


# python imports
import logging
import time

# Connext imports
import rti.connextdds as dds

from Connext import Connext
from InstanceGen import InstanceGen
from Shape import Shape

LOG = logging.getLogger(__name__)


class ConnextSubscriber(Connext):
    """Subscriber can subscribe to one or more shapes"""

    def __init__(self, args, config):
        super().__init__(args)
        self.instance_gen_dic = {}  # Topic-color: InstanceGen
        self.subscriber = dds.Subscriber(self.participant)
        reader_qos = self.qos_provider.datareader_qos
        self.reader_dic = {}
        for which in config.keys():
            LOG.info(f'Subscribing to {which=} {config[which]=}')
            if 1==1:
                self.reader_dic[which] = dds.DynamicData.DataReader(
                    self.subscriber, self.topic_dic[which], reader_qos)
            else:
                self.reader_dic[which] = dds.DataReader(
                    self.participant.implicit_subscriber, self.topic_dic[which])

    def get_max_samples_per_instance(self, which):
        """ helper to fetch depth from a reader"""
        return self.reader_dic[which].qos.resource_limits.max_samples_per_instance

    def start(self, fig, axes):
        """First, some globals and helpers"""
        super().start(fig, axes)

    def handle_one_sample(self, which, sample):
        """update the poly_dic with fresh shape info"""
        """create/update a matplotlib polygon from the sample data, add to poly_dic
           remove the prior poly's edge"""
        self.sample_counter.update(f'{which}r')
        shape = Shape.from_sample(args=self.args, which=which,
                      data=sample.data, info=sample.info)
        instance_gen_key = f'{which}-{shape.color}'  # TODO use API to get Key
        ###LOG.info(f'{sample=} {sample.get_key_value()=}')
        inst = self.instance_gen_dic.get(instance_gen_key)
        if not inst:
            inst = InstanceGen(self.get_max_samples_per_instance(which))
            self.instance_gen_dic[instance_gen_key] = inst
        ix = inst.next()
        LOG.debug(f'SHAPE: {shape=}, {ix=}')
        poly_key = self.form_poly_key(which, shape.color, ix)
        poly = self.poly_dic.get(poly_key)
        if self.args.justdds:
            LOG.info("early exit")
            return
        if not poly:
            poly = shape.create_poly()
            self.poly_dic[poly_key] = poly
            LOG.debug(f'added {poly_key=}')
            self.axes.add_patch(poly)

        xy = shape.get_points()
        if which == 'CP':
            poly.center = xy  ## no attr poly.set_xy(xy) nor property poly.set(center=xy)
        elif which == 'C':
            poly.set(center=xy)
        else:
            poly.set_xy(xy)
        poly.set(lw=self.WIDE_EDGE_LINE_WIDTH, zorder=shape.zorder)

        prev_poly_key = self.form_poly_key(which, shape.color, inst.get_prev_ix())
        prev_poly = self.poly_dic.get(prev_poly_key)
        if prev_poly:
            prev_poly.set(lw=self.THIN_EDGE_LINE_WIDTH)

    def handle_samples(self, reader, which):
        """get samples and handle each"""

        LOG.debug(f'START {self.sample_counter=}')
        with reader.take_valid() as samples:
            for sample in samples:
                self.handle_one_sample(which, sample)

        if self.args.nap:
            time.sleep(self.args.nap)
            LOG.info(f'Sleeping {self.args.nap=}')

        LOG.debug(f'{self.sample_counter=}')

    def fetch_and_draw(self, _):
        """The animation function, called periodically in a set interval, reads the
        last image received and draws it"""
        readers = self.reader_dic.values()
        whiches = self.reader_dic.keys()
        for reader, which in zip(readers, whiches):
            self.handle_samples(reader, which)

        return self.poly_dic.values()  # give back the updated values so they are rendered
