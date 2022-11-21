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
from io import StringIO
import sys

from Shape import COLOR_MAP

LOG = logging.getLogger(__name__)

# Strategy:
# keep sub & pub separate even though only one is used at a time
# key dic by which & color to allow for different settings by shape & color
# Population
# start with empty pub and sub dictionaries
# apply any config file on top
# if any shape entry
# start with defaults
# override with file values
# override with any cmd-line values
# mark either pub or sub active by clearing the other

FILL_KIND_LIST = ['SOLID', 'EMPTY', 'HORIZONTAL', 'VERTICAL']


class ConfigParser:
    """parse the JSON config file populating a sub or pub dic"""

    def __init__(self, defaults):
        self.defaults = defaults
        self.pub_dic = {}  # holds normalized publisher data  TODO: keyed by Shape-Color
        self.pub_dic_default = {}
        self.pub_dic_help = {}
        self.sub_dic = {}  # holds normalized subscriber data
        self.sub_dic_default = {}
        self.sub_dic_help = {}

        self._pub_default_and_help('xy', (50, 50), 'Starting xy position')
        self._pub_default_and_help(
            'delta_xy', (5, 5), 'Center x and y increment per update')

        color_list = COLOR_MAP.keys()
        trans = str.maketrans("", "", "'dict_keys()[]")
        colors = str(color_list).translate(trans)
        self._pub_default_and_help('color', defaults['COLOR'], 'Shape color: ' + colors)
        self._pub_default_and_help('shapesize', 30, 'Size of shape in pixels')
        self._pub_default_and_help('fillKind', 0,
                                  ('Fill pattern of the shape: ' + 
                                   '[0 (solid)], 1 (empty), 2 (horizontal), 3 (vertical)'))
        self._pub_default_and_help('angle', 0, 'Shape rotation angle')
        self._pub_default_and_help(
            'delta_angle', 0, 'Rotation angle increment per update')
        # self.pub_default_and_help('reliability_type', 'best',
        #                           'type of reliability: best, reliable')

        # self.sub_default_and_help('reliability_type', 'best',
        #                          'type of reliability: best, reliable')
        self._sub_default_and_help('content_filter', None,
                                   'Filter region tuple (top-left, bottom-right vertices)')

    @staticmethod
    def _default_and_help(value_dic, help_dic, key, value, help_text):
        value_dic[key] = value
        help_dic[key] = help_text

    def _sub_default_and_help(self, key, value, help_text):
        """add key, value, help to dictionaries"""
        self._default_and_help(self.sub_dic_default,
                               self.sub_dic_help, key, value, help_text)

    def _pub_default_and_help(self, key, value, help_text):
        """add key, value, help to dictionaries"""
        self._default_and_help(self.pub_dic_default,
                               self.pub_dic_help, key, value, help_text)

    def get_pub_config(self, default=False):
        """public getter for pub config"""
        return (self.pub_dic_default, self.pub_dic_help) if default else self.pub_dic

    def get_sub_config(self, default=False):
        """public getter for sub config"""
        return (self.sub_dic_default, self.sub_dic_help) if default else self.sub_dic

    ### Checkers and normalizers
    @staticmethod
    def normalize_shape(shape):
        letter = shape[0].upper()
        valid_letters = ['C', 'S', 'T']
        if letter not in valid_letters:
            raise ValueError(
                f'Shape first letter must be in {valid_letters} not {shape}')
        return letter

    @staticmethod
    def is_shapesize(txt):
        return txt.upper()[-4:] == 'SIZE'

    @staticmethod
    def is_fill(txt):
        """@return True iff passed the fillKind label"""
        return txt.upper()[0:4] == 'FILL'

    @staticmethod
    def normalize_fill(txt):  # TODO use ShapeTypeExtended intEnum
        """@return the normalized fill attribute or throw"""
        normalized = None
        if isinstance(txt, str):
            s_upper = txt.upper()
            for ix, kind in enumerate(FILL_KIND_LIST):
                if s_upper == kind:
                    normalized = ix
                    break
            else:  # python for..else
                ValueError(f'fillKind must be in: {FILL_KIND_LIST} not {txt}')
        else:
            try:
                normalized = int(txt)
            except Exception as exc:
                raise ValueError(
                    f'fillKind must be in range 0-{len(FILL_KIND_LIST)} not {txt}') from exc
        return normalized

    @staticmethod
    def normalize_int(param, value):
        """Raise if value cannot be made int"""
        try:
            normalized = int(value)
        except Exception as exc:
            raise ValueError(
                f'argument to {param} parameter must be an integer, not {value}') from exc
        return normalized

    @staticmethod
    def normalize_float(param, value):
        """Raise if value cannot be made a float"""
        try:
            normalized = float(value)
        except Exception as exc:
            raise ValueError(
                f'argument to {param} parameter must be a float, not {value}') from exc
        return normalized

    def normalize_xy(self, param, value):
        """Raise if there's something wrong"""
        if (not isinstance(value, tuple) and not isinstance(value, list)) or len(value) != 2:
            raise ValueError(
                f'argument to {param} parameter must be a (x, y) tuple not {value}')
        LOG.debug(f'{param=} {value=} {type(value)=} {type(value[0])=}')
        try:
            normalized = int(value[0]), int(value[1])
        except Exception as exc:
            raise ValueError(f'argument to {param} parameter \
                               must be a (x, y) tuple of floats not {value}') from exc
        return normalized
    # end Checkers and normalizers

    def parse(self, stream_or_filename=None):
        """parsing user-entered config data, so tolerate mixed case"""
        # Validate the keys but let the values flow to the dic consumer
        if not stream_or_filename:
            return
        if isinstance(stream_or_filename, str):
            with open(stream_or_filename, 'r') as cfg_file:
                cfg_dic = json.load(cfg_file)
        elif isinstance(stream_or_filename, StringIO):
            cfg_dic = json.loads(stream_or_filename.getvalue())
        else:
            raise ValueError(
                f'parameter must be StringIO or str, not {type(stream_or_filename)=}')

        for act in cfg_dic.keys():
            action = act[0:3].upper()
            if "PUB" == action:
                self.parse_pub(cfg_dic[act])
            elif "SUB" == action:
                self.parse_sub(cfg_dic[act])

    def parse_sub(self, cfg):
        """parse the sub dictionary"""
        LOG.debug(f'sub {cfg=}')
        for shape in cfg.keys():
            n_shape = self.normalize_shape(shape)
            self.sub_dic[n_shape] = self.sub_dic_default
        LOG.debug(f'{self.sub_dic=}')

    def parse_pub(self, cfg):
        """parse the pub dictionary"""
        #LOG.info(f'pub {cfg=} {cfg.keys()=}')
        #print(f'pub {cfg=} {cfg.keys()=}')
        if len(cfg.keys()) > 1:
            LOG.warning("Only the first shape's config will be used.  Publishing multiple shapes is TBD")
        for shape in cfg.keys():
            n_shape = self.normalize_shape(shape)
            self.pub_dic[n_shape] = self.pub_dic_default
            for attr in cfg[shape].keys():
                attr_upper = attr.upper()
                value = cfg[shape][attr]
                if isinstance(value, str):
                    value = value.upper()
                if attr_upper == "COLOR":
                    self.pub_dic[n_shape]['color'] = value
                elif self.is_shapesize(attr_upper):
                    self.pub_dic[n_shape]['shapesize'] = self.normalize_int(
                        'shapesize', value)
                elif attr_upper == "ANGLE":
                    self.pub_dic[n_shape]['angle'] = self.normalize_float(
                        'angle', value)
                elif self.is_fill(attr_upper):
                    if isinstance(value, str):
                        value = self.normalize_fill(value)
                    self.pub_dic[n_shape]['fill'] = value
                #elif attr_upper == "RELIABILITY_TYPE":
                    #self.pub_dic[n_shape]['reliability_type'] = value
                elif attr_upper == "XY":
                    self.pub_dic[n_shape]['xy'] = self.normalize_xy(
                        'xy', value)
                elif attr_upper == "DELTA_XY":
                    self.pub_dic[n_shape]['delta_xy'] = self.normalize_xy(
                        'delta_xy', value)
                elif attr_upper == "DELTA_ANGLE":
                    self.pub_dic[n_shape]['delta_angle'] = self.normalize_float(
                        'delta_angle', value)
            break  # ignore all but first

            #if self.pub_dic[n_shape]["color"] != self.defaults.color:
        LOG.debug(f'{self.pub_dic=}')

    def get_config(self, parsed_args):
        """prepare config from config or command-line"""
        is_pub, config = False, {}
        if parsed_args.config:
            parsed_args.publish = parsed_args.subscribe = None
            pub_cfg = self.get_pub_config()
            sub_cfg = self.get_sub_config()
            LOG.debug(f'{pub_cfg=} {sub_cfg=}')
            if pub_cfg and sub_cfg:
                LOG.warning("Both pub and sub found, ignoring publisher")
            if sub_cfg:
                config = sub_cfg
            else:
                config = pub_cfg
                is_pub = True
        # config OR command-line - sub OR pub only
        elif parsed_args.subscribe:
            for which in parsed_args.subscribe:
                defaults, _ = self.get_sub_config(default=True)
                config[which] = defaults
        elif parsed_args.publish:
            is_pub = True
            for which in parsed_args.publish:
                defaults, _ = self.get_pub_config(default=True)
                config[which] = defaults
        else:
            LOG.error("Must run as either publisher or subscriber, terminating")
            sys.exit(-1)
        return parsed_args, is_pub, config
