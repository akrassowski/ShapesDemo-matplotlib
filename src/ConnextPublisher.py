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

    def __init__(self, args, config=None):
        super().__init__(args)
        LOG.info(f'{args=} {config=}')
        self.publisher = dds.Publisher(self.sparticipant)
        #writer_qos = self.qos_provider.datawriter_qos  ## TODO: use me
        self.pub_dic = {}  # defaults will be keyd by just shape; actual will be shape-color
        self.sample_dic = {}
        self.writer_dic = {}
        self.pub_key_count = 1
        if config:
            LOG.debug(f'{config=}')
            for key in config.keys():
                #LOG.debug(f'{self.stopic_dic=} \n{self.participant=}')
                #shape, color = self.key_to_topic_and_color(key)
                key = key[0]
                self.writer_dic[key] = dds.DataWriter(self.publisher, self.stopic_dic[key])
            self.pub_dic = config
        LOG.info(f'ConnextPublisher starting: {self.pub_dic=}')


    def start(self, fig, axes):
        """First, some globals and helpers"""
        super().start(fig, axes)

    @staticmethod
    def key_to_topic_and_color(text):
        result = text.split(DELIM)
        return result

    @staticmethod
    def form_pub_key(normalized_shape, normalized_color):
        key = f'{normalized_shape}{DELIM}{normalized_color}'
        return key

    def create_default_sample(self, which):
        """use the defaults to create a sample"""
        #print(f'{which=} {self.pub_dic=}')
        LOG.debug(f'{which=}')
        sample = ShapeTypeExtended()
        defaults = self.pub_dic[which]  # just shape for defaults
        sample.x, sample.y = defaults['xy']
        sample.color = defaults['color']
        sample.shapesize = defaults['shapesize']
        sample.extended = defaults['extended']
        sample.fillKind = defaults['fillKind']
        sample.angle = defaults['angle']
        return sample


    def publish_sample(self, key):
        which, color = self.key_to_topic_and_color(key)
        self.sample_counter.update(f'{which}w')
        sample = self.sample_dic.get(which)
        new_sample = True
        if sample:
            new_sample = False
        else:
            sample = self.create_default_sample(key)
            LOG.debug(f'NEW {sample=}')

        shape = Shape.from_pub_sample(
            which=which,
            limit_xy=self.args.graph_xy,
            sample=sample
        )
        LOG.debug(f'{shape=}')
        if not new_sample:
            LOG.debug(f'PUBDIC: {self.pub_dic[key]=}')
            xy, delta_xy = shape.reverse_if_wall(self.pub_dic[key]['delta_xy'])
            sample.x, sample.y = xy[0], Shape.mpl2sd(xy[1], self.args.graph_xy[1])
            # save the modified direction
            self.pub_dic[key]['delta_xy'] = delta_xy
            shape.xy = xy
            shape.angle += self.pub_dic[key]['delta_angle']
            self.pub_dic[key]['angle'] += self.pub_dic[key]['delta_angle']
            LOG.debug(f'set_xy {key=} {xy=} {shape.angle=}')
        poly_key = self.form_poly_key(which, shape.color)
        poly = self.poly_dic.get(poly_key)
        points = shape.get_points()

        self.writer_dic[which].write(sample)  ## publish the sample
        self.sample_dic[which] = sample       ##   and remember it
        LOG.debug('sample:%s', self.sample_dic[which])
        if not poly:
            poly = shape.create_poly()
            self.poly_dic[poly_key] = poly
            LOG.debug(f"added {poly_key=}")
            if self.args.justdds:
                LOG.warning("justdds: early exit")
                return
            self.axes.add_patch(poly)
            test_text = False
            if test_text:
                text = "?"
                txt = self.axes.text(70, 70, text, fontsize=15)
                self.poly_dic['text1'] = txt

        Shape.set_poly_center(poly, which, points)
        # update the plot
        poly.set(lw=self.THIN_EDGE_LINE_WIDTH, zorder=shape.zorder)


    def fetch_and_draw(self, _):
        """callback for matplotlib to update shapes"""
        for key in self.pub_dic.keys():
            self.publish_sample(key)

        return self.poly_dic.values()
