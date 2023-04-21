#!/usr/bin/env python

###############################################################################
# (c) Copyright, Real-Time Innovations, 2021. All rights reserved.            #
# No duplications, whole or partial, manual or electronic, may be made        #
# without express written permission.  Any such copies, or revisions thereof, #
# must display this notice unaltered.                                         #
# This code contains trade secrets of Real-Time Innovations, Inc.             #
###############################################################################

"""Produce a config by parsing a config file or from the cmd-line"""

# python imports
import copy
import json
import logging
from pprint import pformat
from io import StringIO
import sys
import textwrap

from shape import COLOR_MAP

LOG = logging.getLogger(__name__)

# Strategy:
# keep sub & pub separate even though only one is used at a time
# key list of dic by which & color to allow for different settings by shape & color
# Population
# parse into list of pub dic and single sub_dic
# validate attributes; a dup = error
# fill in missing with defaults

FILL_KIND_LIST = ['SOLID', 'EMPTY', 'HORIZONTAL', 'VERTICAL']
VALID_SHAPE_LETTERS = 'CST'

class ConfigParser:
    """parse the JSON config file populating a sub or pub dic"""

    # pylint: disable=too-many-instance-attributes
    def __init__(self, defaults):
        self.pub_list = []  # list of pub dicts
        self.pub_default_dic = {}
        self.pub_help_dic = {}
        self.pub_attr = []

        self.sub_dic = {}
        self.sub_default_dic = {}
        self.sub_help_dic = {}
        self.sub_attr = []
        self.init_defaults(defaults)

    def init_defaults(self, defaults):
        """Helper to initialize a shape's default values as byproduct of help"""
        self._default_and_help(self.pub_default_dic, self.pub_help_dic, self.pub_attr,
            key='xy', value=[50, 50], help_='Starting xy position')
        self._default_and_help(self.pub_default_dic, self.pub_help_dic, self.pub_attr,
            key='delta_xy', value=[5, 5], help_='Center x and y change per update')

        trans = str.maketrans("", "", "'dict_keys()[]")
        colors = str(COLOR_MAP.keys()).translate(trans)
        self._default_and_help(self.pub_default_dic, self.pub_help_dic, self.pub_attr,
            key='color', value=defaults['COLOR'], help_='Shape color: ' + colors)
        self._default_and_help(self.pub_default_dic, self.pub_help_dic, self.pub_attr,
            key='shapesize', value=30, help_='Size of shape in pixels')
        self._default_and_help(self.pub_default_dic, self.pub_help_dic, self.pub_attr,
            key='fillKind', value=0,
            help_=('Fill pattern of the ShapeExtendedType: ' +
                  '[0 (solid)], 1 (empty), 2 (horizontal), 3 (vertical)'))
        self._default_and_help(self.pub_default_dic, self.pub_help_dic, self.pub_attr,
            key='angle', value=0, help_='Starting angle for ShapeExtendedType')
        self._default_and_help(self.pub_default_dic, self.pub_help_dic, self.pub_attr,
            key='delta_angle', value=2, help_='Rotation change per update for ShapeExtendedType')

        self._default_and_help(self.sub_default_dic, self.sub_help_dic, self.sub_attr,
                               key='content_filter_xy', value=None,
                               help_=textwrap.dedent("""Filter region defined by x, y tuples [None]
                               Tuples define the (top-left, bottom-right) vertices.
                               x, y values are inclusive to the filter region."""))
        self._default_and_help(self.sub_default_dic, self.sub_help_dic, self.sub_attr,
                               key='content_filter_color', value=None,
                               help_='Filter for a specific color')
        self._default_and_help(self.sub_default_dic, self.sub_help_dic, self.sub_attr,
                               key='content_filter_include', value=True,
                               help_='Specify filter mode, 0 to exclude [1] to include."')

    @staticmethod
    # pylint: disable=too-many-arguments
    def _default_and_help(ps_default_dic, ps_help_dic, ps_attr_list, key, value, help_):
        """add key, value, help to either pub or sub dictionaries"""
        ps_default_dic[key] = value
        ps_help_dic[key] = help_
        ps_attr_list.append(key)

    def get_pub_config(self, default=False):
        """public getter for pub config"""
        return (self.pub_default_dic, self.pub_help_dic) if default else self.pub_list

    def get_sub_config(self, default=False):
        """public getter for sub config"""
        ## return (self.sub_default_dic, self.sub_help_dic) if default else self.sub_list
        return (self.sub_default_dic, self.sub_help_dic) if default else self.sub_dic

    ### Checkers and normalizers
    @staticmethod
    def _err_msg(param, desired, value):
        """Helper to format an error message"""
        return f'{param} must be {desired} not {value}'

    @staticmethod
    def normalize_shape(shape):
        """@return the normalized shape letter"""
        letter = shape[0].upper()
        if letter not in VALID_SHAPE_LETTERS:
            raise ValueError(
                ConfigParser._err_msg('Shape first letter',  f'in {VALID_SHAPE_LETTERS}', shape))
        return letter

    @staticmethod
    def is_shapesize(txt):
        return txt[-4:] == 'SIZE'

    @staticmethod
    def is_fill(txt):
        """@return True iff passed the fillKind label"""
        return txt[0:4] == 'FILL'

    @staticmethod
    def is_content_filter_color(u_txt):
        """@return True iff content filter is specified"""
        return 'FILTER_COLOR' in u_txt

    @staticmethod
    def is_content_filter_xy(u_txt):
        """@return True iff content filter is specified"""
        return 'FILTER_XY' in u_txt

    @staticmethod
    def is_content_filter_include(u_txt):
        """@return True iff content filter is specified"""
        return 'FILTER_INCLUDE' in u_txt

    @staticmethod
    def normalize_fill(value):  # TODO use ShapeTypeExtended intEnum
        """@return the normalized fill attribute or throw"""
        if isinstance(value, str):
            try:
                normalized = FILL_KIND_LIST.index(value.upper())
            except ValueError as exc:
                raise ValueError(
                    ConfigParser._err_msg('fillKind', f'in: {FILL_KIND_LIST}', value)) from exc
        elif isinstance(value, int):
            limit = len(FILL_KIND_LIST) - 1
            if value < 0 or value > limit:
                phrase = f'in range 0-{limit}'
                raise ValueError(ConfigParser._err_msg('fillKind', phrase, value))
            normalized = value
        else:
            raise ValueError(ConfigParser._err_msg('fillKind', 'int or string', value))
        return normalized

    @staticmethod
    def normalize_bool(value):
        """Allow 'False' and '0' to be False"""
        normalized = bool(value)
        if isinstance(value, str):
            u_value = value.upper()
            if u_value in ('FALSE', '0'):
                normalized = False
        return normalized

    @staticmethod
    def normalize_int(param, value):
        """Raise if value cannot be made int"""
        try:
            normalized = int(value)
        except Exception as exc:
            raise ValueError(ConfigParser._err_msg(param, "an integer", value)) from exc
        return normalized

    @staticmethod
    def normalize_float(param, value):
        """Raise if value cannot be made a float"""
        try:
            normalized = float(value)
        except Exception as exc:
            raise ValueError(ConfigParser._err_msg(param, "a float", value)) from exc
        return normalized

    def normalize_xy(self, param, value):
        """Raise if there's something wrong"""
        if (not isinstance(value, tuple) and not isinstance(value, list)) or len(value) != 2:
            raise ValueError(self._err_msg(param, "a (x, y) list", value))
        try:
            normalized = [int(value[0]), int(value[1])]  # list not tuple so updates can be assigned
        except Exception as exc:
            raise ValueError(self._err_msg(param, "a [x, y] list of int", value)) from exc
        return normalized
    # end Checkers and normalizers

    def json_to_config(self, stream_or_fname=None):
        """parsing user-entered config data, so tolerate mixed case"""
        # Validate the keys but let the values flow to the dic consumer
        def _dict_decorate(ordered_pairs):
            """flatten dups by appending count"""
            dic, count = {}, 1
            for key, value in ordered_pairs:
                if key in dic:
                    dic[f'{key}_{count}'] = value
                    count += 1
                else:
                    dic[key] = value
            return dic

        if isinstance(stream_or_fname, str):
            with open(stream_or_fname, 'r', encoding='utf8') as cfg_file:
                cfg_dic = json.load(cfg_file, object_pairs_hook=_dict_decorate)
        elif isinstance(stream_or_fname, StringIO):
            cfg_dic = json.loads(stream_or_fname.getvalue(), object_pairs_hook=_dict_decorate)
        else:
            raise ValueError(
                self._err_msg('param', 'must be StringIO or str', type(stream_or_fname)))
        return cfg_dic

    def parse(self, stream_or_fname=None):
        """parsing user-entered config data, so tolerate mixed case"""
        if not stream_or_fname:
            return
        cfg_dic = self.json_to_config(stream_or_fname)
        for key in cfg_dic.keys():
            key_upper = key.upper()
            if "PUB" in key_upper:
                self.parse_pub(cfg_dic[key])
                ##self.parse_pub(cfg_dic[key], key)
            elif "SUB" in key_upper:
                self.parse_sub(cfg_dic[key])

    def parse_pub(self, cfg):
        """fail on dup attributes, synthesize required with defaults"""
        for key in cfg.keys():
            which = self.normalize_shape(key)
            parsed = self.parse_one_pub(which, cfg[key])
            self.pub_list.append(parsed)
            LOG.info('which:%s parsed:%s', which, parsed)
        LOG.info(pformat(self.pub_list))

    def parse_sub(self, cfg):
        """parse the sub dictionary, saving as self.sub_dic to be retrieved with get_sub_config"""
        LOG.info('cfg:%s ', cfg)
        # breakpoint()
        for shape in cfg.keys():
            n_shape = self.normalize_shape(shape)
            self.sub_dic[n_shape] = copy.copy(self.sub_default_dic)  # ensures key is present
            for attr in cfg[shape].keys():
                value = cfg[shape][attr]
                attr_upper = attr.upper()
                if self.is_content_filter_xy(attr_upper):
                    self.sub_dic[n_shape]['content_filter_xy'] = value
                elif self.is_content_filter_color(attr_upper):
                    self.sub_dic[n_shape]['content_filter_color'] = value.upper()
                elif self.is_content_filter_include(attr_upper):
                    self.sub_dic[n_shape]['content_filter_include'] = self.normalize_bool(value)
        LOG.info('sub_dic: %s', self.sub_dic)

    def parse_one_pub(self, which, cfg):
        """@return pub_dic by parsing a pub dictionary"""
        LOG.info('pub cfg: %s', cfg)
        # start with default, overwrite as needed
        pub_dic = copy.copy(self.pub_default_dic)
        pub_dic['which'] = which
        for attr in cfg.keys():
            attr_upper = attr.upper()
            value = cfg[attr]
            if isinstance(value, str):
                value = value.upper()
            if attr_upper == "COLOR":
                color = value
                pub_dic['color'] = color
            elif self.is_shapesize(attr_upper):
                pub_dic['shapesize'] = self.normalize_int('shapesize', value)
            elif attr_upper == "ANGLE":
                pub_dic['angle'] = self.normalize_float('angle', value)
            elif self.is_fill(attr_upper):
                value = self.normalize_fill(value)
                pub_dic['fillKind'] = value
            elif attr_upper == "XY":
                pub_dic['xy'] = self.normalize_xy('xy', value)
            elif attr_upper == "DELTA_XY":
                pub_dic['delta_xy'] = self.normalize_xy('delta_xy', value)
            elif attr_upper == "DELTA_ANGLE":
                pub_dic['delta_angle'] = self.normalize_float('delta_angle', value)

        LOG.info(pub_dic)
        return pub_dic

    def get_config(self, parsed_args):
        """prepare config from config or command-line"""
        is_pub, config = False, {}
        if parsed_args.config:
            parsed_args.publish = parsed_args.subscribe = None
            pub_cfg = self.get_pub_config()
            sub_cfg = self.get_sub_config()
            #LOG.info(f'{pub_cfg=} \n {sub_cfg=}')
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
            for ix, which in enumerate(parsed_args.publish):
                defaults, _ = self.get_pub_config(default=True)
                config.update(defaults)
                config['which'] = which
                config['delta_xy'] = [config['delta_xy'][0] + ix, config['delta_xy'][1] + ix]
                self.pub_list.append(copy.copy(config))
            config = self.pub_list
        else:
            LOG.error("Must run as either publisher or subscriber, terminating")
            sys.exit(-1)
        LOG.info(config)
        return parsed_args, is_pub, config
