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
from pprint import pformat
# Connext imports
import rti.connextdds as dds
# It is required that the rtiddsgen be alreay run to create the type class
# The generated <datatype>.py class file should be included here
from ShapeTypeExtended import ShapeType, ShapeTypeExtended

from connext import Connext, possibly_log_qos
from shape import Shape

LOG = logging.getLogger(__name__)

"""
Sample   SD - published by Publisher's DataWriter;
              contains the IDL's values, i.e. separate x, y values, y is "reversed", size is halved
pub_dic     - holds meta-attributes i.e. delta_xy, (initial)xy, delta_angle
Shape   MPL - holds matplotlib attributes, like points (vertices) and center xy
Polygon MPL - matplotlib object used to graphically display the shape

240+
   |
200+
   |
150+   matplotlib
   |      axes
100+    MPL Coord
   |
 50+
   |
  0+--+--+--+--+--+--+--
   0 50 100 150 200 240


  0+
   |
 50+
   |
100+    ShapesDemo
   |      axes
150+    SD Coord
   |
200+
   |
240+--+--+--+--+--+--+--
   0 50 100 150 200 240
"""

class ConnextPublisher(Connext):
    """Publish only 1 shape for now"""

    def __init__(self, matplotlib, args, config_list=None):
        super().__init__(matplotlib, args)
        LOG.info('args=%s config_list=%s', args, config_list)
        #writer_qos = self.qos_provider.datawriter_qos  ## TODO: use me
        self.publisher = dds.Publisher(self.participant_with_qos)
        possibly_log_qos(self.args.log_qos, self.publisher)
        self.shape_dic = {}  # which: Shape
        self.sample_dic = {}  # which-color: latest-published-sample
        self.writer_dic = {}  # which: dataWriter
        for config in config_list:
            #LOG.debug(f'{self.topic_dic=} \n{self.participant=}')
            LOG.info('config:%s', config)
            key = config['which']
            self.writer_dic[key] = dds.DataWriter(
                self.publisher, self.topic_dic[key], self.rw_qos_provider.datawriter_qos)
            possibly_log_qos(self.args.log_qos, self.writer_dic[key])
        self.pub_config_list = config_list
        LOG.debug('Pub starting - pub_config_list: %s %s', pformat(config_list), self.writer_dic)

    @staticmethod
    def form_pub_key(normalized_shape, normalized_color):
        """format and return a publisher key"""
        return f'{normalized_shape}-{normalized_color}'

    def create_default_sample(self, pub_dic):
        """use the defaults to create a sample"""
        LOG.info('pub_dic=%s', pub_dic)
        sample = ShapeTypeExtended() if self.args.extended else ShapeType()
        LOG.info(pub_dic)
        sample.x, sample.y = pub_dic['xy']
        sample.color = pub_dic['color']
        sample.shapesize = pub_dic['shapesize']
        if self.args.extended:
            sample.fillKind = pub_dic['fillKind']
            sample.angle = pub_dic['angle']
        return sample

    def update_shape(self, shape, sample):
        """helper to wrap extended"""
        shape.update(sample.x, sample.y, sample.angle if self.args.extended else None)

    def publish_sample(self, pub_dic):
        """publish a single sample"""
        which = pub_dic['which']  # only 1 key for now
        key = self.form_pub_key(which, pub_dic.get('color'))  # TODO: refactor defaults?
        self.sample_counter.update([f'{key}-write'])
        sample = self.sample_dic.get(key)
        is_new_sample = sample is None
        if is_new_sample:
            sample = self.create_default_sample(pub_dic)
            LOG.debug('NEW sample=%s', sample)

            shape = Shape.from_pub_sample(
                matplotlib=self.matplotlib,
                which=which,
                sample=sample,
                extended=self.args.extended
            )
            self.shape_dic[which] = shape
        else:
            shape = self.shape_dic[which]
        poly_key = self.form_poly_key(which, shape.color)
        self.update_shape(shape, sample)

        LOG.debug('shape=%s', shape)
        if not is_new_sample:
            ###LOG.debug('PUBDIC: pub_dic[key]=%s', self.pub_dic[key])
            xy, delta_xy = shape.reverse_if_wall(pub_dic['delta_xy'])
            sample.x, sample.y = xy[0], self.matplotlib.flip_y(xy[1])
            # save the modified direction
            pub_dic['delta_xy'] = delta_xy
            if self.args.extended:
                # save mod angle
                sample.angle += pub_dic['delta_angle']
            #LOG.debug(f'SET_XY {key=} {xy=} {shape.angle=}')
        poly = self.poly_dic.get(poly_key)
        points = shape.get_points()
        self.adjust_zorder()

        self.writer_dic[which].write(sample)  ## publish the sample
        self.sample_dic[key] = sample       ##   and remember it
        LOG.debug('sample:%s', self.sample_dic[key])
        if not poly:
            poly = shape.create_poly()
            self.poly_dic[poly_key] = poly
            LOG.debug("added poly_key=%s", poly_key)
            if self.args.justdds:
                LOG.warning("justdds: early exit")
                return
            self.matplotlib.axes.add_patch(poly)
        shape.set_poly_center(poly, which, points)
        # update the plot
        poly.set(lw=self.matplotlib.THIN_EDGE_LINE_WIDTH, zorder=shape.zorder)

    def adjust_zorder(self, limit=500):
        """Periodically, reset the zorder to prevent runaway growth"""
        for child in self.matplotlib.axes.get_children():
            if child.zorder > limit:
                for child2 in self.matplotlib.axes.get_children():
                    if child2.zorder > 10:  # skip base zorder items
                        child2.set(zorder=int(child2.zorder/2))
                Shape.shared_zorder = int(Shape.shared_zorder / 2)
                break

    def draw(self, _):
        """callback for matplotlib to update shapes"""
        for pub_dic in self.pub_config_list:
            self.publish_sample(pub_dic)
        return self.poly_dic.values()

    def __repr__(self):
        return ('<ConnextPublisher:\n' +
                f'  pub_config_list: {self.pub_config_list}\n' +
                f'  shapes: {self.shape_dic}\n' +
                f'  samples: {self.sample_dic}\n' +
                f'  writers: {self.writer_dic}' +
                '> ')
        #self.publisher = dds.Publisher(self.participant_with_qos)
