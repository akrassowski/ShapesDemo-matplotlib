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
from ShapeTypeExtended import ShapeType, ShapeTypeExtended

from Connext import Connext
from Shape import Shape

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

DELIM = ';'

class ConnextPublisher(Connext):
    """Publish only 1 shape for now"""

    def __init__(self, matplotlib, args, config=None):
        super().__init__(matplotlib, args)
        LOG.info('args=%s config=%s', args, config)
        #writer_qos = self.qos_provider.datawriter_qos  ## TODO: use me
        self.publisher = dds.Publisher(self.participant_with_qos)
        self.pub_dic = {}  # defaults will be keyd by just shape; actual will be shape-color
        self.shape_dic = {}  # which: Shape
        self.sample_dic = {}  # which-color: latest-published-sample
        self.writer_dic = {}  # which: dataWriter
        self.pub_key_count = 1
        if config:
            for key in config.keys():
                #LOG.debug(f'{self.stopic_dic=} \n{self.participant=}')
                #shape, color = self.key_to_topic_and_color(key)
                key = key[0]
                self.writer_dic[key] = dds.DataWriter(self.publisher, self.stopic_dic[key])
            self.pub_dic = config
        LOG.info('ConnextPublisher starting: pub_dic=%s', self.pub_dic)

    @staticmethod
    def key_to_topic_and_color(text):
        """@return tuple of topic (which) and color"""
        result = text.split(DELIM)
        return result if len(result) > 1 else (result[0], 'BLUE')

    @staticmethod
    def form_pub_key(normalized_shape, normalized_color):
        return f'{normalized_shape}{DELIM}{normalized_color}'

    def create_default_sample(self, which):
        """use the defaults to create a sample"""
        #print(f'{which=} {self.pub_dic=}')
        LOG.debug('which=%s', which)
        sample = ShapeTypeExtended() if self.args.extended else ShapeType()
        defaults = self.pub_dic[which]  # just shape for defaults
        sample.x, sample.y = defaults['xy']
        sample.color = defaults['color']
        sample.shapesize = defaults['shapesize']
        if self.args.extended:
            sample.fillKind = defaults['fillKind']
            sample.angle = defaults['angle']
        return sample

    def update_shape(self, shape, sample):
        """helper to wrap extended"""
        shape.update(sample.x, sample.y, sample.angle if self.args.extended else None)

    def publish_sample(self, key):
        """publish a single sample"""
        which, _ = self.key_to_topic_and_color(key)
        self.sample_counter.update([f'{key}w'])
        sample = self.sample_dic.get(key)
        is_new_sample = sample is None
        if is_new_sample:
            sample = self.create_default_sample(key)
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
            LOG.debug('PUBDIC: pub_dic[key]=%s', self.pub_dic[key])
            xy, delta_xy = shape.reverse_if_wall(self.pub_dic[key]['delta_xy'])
            sample.x, sample.y = xy[0], shape.mpl2sd(xy[1])
            # save the modified direction
            self.pub_dic[key]['delta_xy'] = delta_xy
            if self.args.extended:
                # save mod angle
                sample.angle += self.pub_dic[key]['delta_angle']
            #LOG.debug(f'SET_XY {key=} {xy=} {shape.angle=}')
        poly = self.poly_dic.get(poly_key)
        points = shape.get_points()
        self.adjust_zorder(500)

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
        poly.set(lw=self.THIN_EDGE_LINE_WIDTH, zorder=shape.zorder)

    def adjust_zorder(self, limit):
        for child in self.matplotlib.axes.get_children():
            if child.zorder > limit:
                for child2 in self.matplotlib.axes.get_children():
                    child2.set(zorder=int(child2.zorder/2))
                Shape.shared_zorder = int(Shape.shared_zorder / 2)
                break

    def draw(self, _):
        """callback for matplotlib to update shapes"""
        for key in self.pub_dic.keys():
            self.publish_sample(key)
            self.sleep_as_needed()
        return self.poly_dic.values()
