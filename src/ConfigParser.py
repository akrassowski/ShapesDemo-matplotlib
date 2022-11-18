#!/usr/bin/env python

###############################################################################
# (c) Copyright, Real-Time Innovations, 2021. All rights reserved.            #
# No duplications, whole or partial, manual or electronic, may be made        #
# without express written permission.  Any such copies, or revisions thereof, #
# must display this notice unaltered.                                         #
# This code contains trade secrets of Real-Time Innovations, Inc.             #
###############################################################################

"""Parses a config file"""


# python imports
import json
import logging
import os
import sys
import time

# It is required that the rtiddsgen be alreay run to create the type class
# The generated <datatype>.py class file should be included here
from ShapeTypeExtended import ShapeType, ShapeTypeExtended
from Shape import Shape

LOG = logging.getLogger(__name__)


class ConfigParser:

    def __init__(self, filename):
        self.filename = filename
        self.pub_dic = {}  ## holds normalized publisher data
        self.sub_dic = {}  ## holds normalized subscriber data
        self.pub_dic_default = {}
        self.pub_dic_help = {}
        self.sub_dic_default = {}
        self.sub_dic_help = {}

        self.pub_default_and_help('xy', (50, 50), 'starting xy position')
        self.pub_default_and_help('delta_xy', (5, 5), 'update delta x and y')
        
        color_list = Shape.COLOR_MAP.keys()
        trans = str.maketrans("", "", "'dict_keys()[]")
        colors = str(color_list).translate(trans)
        self.pub_default_and_help('color', 'BLUE', 'Shape color: BLUE, CYAN, GREEN, MAGENTA, ORANGE, PURPLE, RED, YELLOW')
        self.pub_default_and_help('color', 'BLUE', 'Shape color: ' + colors)
        self.pub_default_and_help('shapesize', 30, 'size of shape in pixels')
        self.pub_default_and_help('fillKind', '0 (solid)', 'Fill pattern of the shape: 0 (solid), 1 (empty), 2 (horizontal), 3 (vertical)')
        self.pub_default_and_help('angle', 0, 'Shape rotation angle')
        self.pub_default_and_help('delta_angle', 0, 'Increment for rotation angle')
        self.pub_default_and_help('reliability_type', 'best', 'type of reliability: best, reliable')

        self.sub_default_and_help('reliability_type', 'best', 'type of reliability: best, reliable')
        self.sub_default_and_help('content_filter', None, 'tuple of xy (top-left, bottom-right) region')
        if filename:
            self.parse()

    @staticmethod
    def _default_and_help(value_dic, help_dic, key, value, help_text):
        """helper to add value and help_text to dictionaries"""
        value_dic[key] = value
        help_dic[key] = help_text

    def sub_default_and_help(self, key, value, help_text):
        self._default_and_help(self.pub_dic_default, self.pub_dic_help, key, value, help_text)

    def pub_default_and_help(self, key, value, help_text):
        self._default_and_help(self.sub_dic_default, self.sub_dic_help, key, value, help_text)

    @staticmethod
    def normalize_shape(shape):
        """@return one of C/S/T or raise an exception"""
        letter = shape[0].upper()
        if letter not in 'CST':
            raise ValueError
        return letter
    

    def normalize_xy(self, param, value):
        """Raise if there's something wrong"""
        LOG.debug(f'{param=} {value=} {type(value)=} {type(value[0])=}')
        int_xy = None
        if len(value) != 2:
            raise ValueError(f'argument to {param} parameter must be a (x, y) tuple not {value}')
        try:
            int_xy = int(value[0]), int(value[1])
        except:
            raise ValueError(f'argument to {param} parameter must be a (x, y) tuple of ints not {value}')
        return int_xy

    def get_pub_config(self, default=False):
        """public way to get a publisher's configuration"""
        return self.pub_dic_default, self.pub_dic_help if default else self.pub_dic

    def get_sub_config(self, default=False):
        """public way to get a subscriber's configuration"""
        return self.sub_dic_default, self.sub_dic_help if default else self.sub_dic

    @staticmethod
    def is_shapesize(s):
        return s.upper()[-4:] == 'SIZE'

    @staticmethod
    def is_fillkind(s):
        return s.upper()[0:4] == 'FILL'

    @staticmethod
    def is_color(s):
        return s.upper() == 'COLOR'

    def parse(self):
        """parsing user-entered config data, so tolerate mixed case"""
        """Validate the keys but let the values flow to the dic consumer"""
        with open(self.filename, 'r') as cfg_file:
            cfg = json.load(cfg_file)

        for act in cfg.keys():
            action = act[0:3].upper()
            if "PUB" == action: 
                self.parse_pub(cfg[act])
            elif "SUB" == action: 
                self.parse_sub(cfg[act])
        

    def parse_sub(self, cfg):
        """parse the sub dictionary"""
        LOG.info('sub')
        for shape in cfg[act].keys():
            n_shape = self.normalize_shape(shape)
            self.sub_dic[n_shape] = self.sub_dic_default
    
    def parse_pub(self, cfg):
        """parse the pub dictionary"""
        LOG.info(f'pub {cfg=}')
        for shape in cfg.keys():
            n_shape = self.normalize_shape(shape)
            self.pub_dic[n_shape] = self.pub_dic_default
            for attr in cfg[shape].keys():
                attr_upper = attr.upper()
                value = cfg[shape][attr]
                if type(value) is str: 
                    value = value.upper()
                if self.is_color(attr_upper):
                    self.pub_dic[n_shape]['color'] = value
                elif self.is_shapesize(attr_upper):
                    self.pub_dic[n_shape]['shapesize'] = float(value)
                elif attr_upper == "ANGLE":
                    self.pub_dic[n_shape]['angle'] = float(value)
                elif self.is_fillkind(attr_upper):
                    self.pub_dic[n_shape]['fillkind'] = value
                elif attr_upper == "RELIABILITY_TYPE":
                    self.pub_dic[n_shape]['reliability_type'] = value
                elif attr_upper == "XY":
                    value = self.normalize_xy('xy', value)
                    self.pub_dic['xy'] = value
                elif attr_upper == "delta_xy":
                    value = self.normalize_xy('delta_xy', value)
                    self.pub_dic['delta_xy'] = value

            LOG.info(self.pub_dic)
