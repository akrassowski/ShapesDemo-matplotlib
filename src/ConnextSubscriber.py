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
from collections import defaultdict
import logging

# Connext imports
import rti.connextdds as dds

from Connext import Connext
from InstanceGen import InstanceGen
from Shape import Shape, COLOR_MAP
from ShapeListener import ShapeListener

LOG = logging.getLogger(__name__)

class ConnextSubscriber(Connext):
    """Subscriber can subscribe to one or more shapes"""

    def __init__(self, matplotlib, args, config):
        super().__init__(matplotlib, args)
        self.instance_gen_dic = {}  # Topic-color: InstanceGen
        self.shape_dic = {}  # Topic-color: InstanceGen
        self.reader_dic = {}  # one reader per Shape key: CST values: dds.DataReader
        self.poly_pub_dic = defaultdict(list)  # key: pubHandle values: [poly_key1, poly_key2...]
        self.handles_set = set()
        self.handle_dic = {}
        self.subscriber = dds.Subscriber(self.participant_with_qos)
        self.possibly_log_qos(self.subscriber)
        reader_qos = self.qos_provider.datareader_qos

        listener = ShapeListener()
        status_mask = listener.get_mask()
        for which in config.keys():
            LOG.info(f'Subscribing to {which=} {config[which]=}')
            topic = self._init_get_topic(which, config)
            self.reader_dic[which] = dds.DataReader(
                self.subscriber,
                topic,
                reader_qos,
                listener,
                status_mask
            )
            self.handle_dic[which] = str(self.reader_dic[which].instance_handle)
            self.possibly_log_qos(self.reader_dic[which])

    def _init_get_topic(self, which, config):
        """get a Content Filtered or normal Topic"""
        topic = self.stopic_dic[which]
        cfxy = config[which].get('content_filter_xy')
        if cfxy:
            topic = self._init_content_filter_xy(topic, which, cfxy)
        else:
            cfcolor = config[which].get('content_filter_color')
            if cfcolor:
                topic = self._init_content_filter_color(topic, which, cfcolor)
        return topic

    def _init_content_filter_xy(self, topic, which, cfxy):
        """handle filter region with top-left and bottom-right specified"""
        hatch_pattern = { 'c': 'o', 'T': '/', 'S': '+'}
        expr = "x >= %0 AND y >= %1 AND x <= %2 and y <= %3"
        params = [str(n) for sublist in cfxy for n in sublist]
        topic = dds.ContentFilteredTopic(topic, f"CFTxy-{which}", dds.Filter(expr, params))
        anchor = (
            min(cfxy[0][0], cfxy[1][0]),
            #min(self.matplotlib.flip_y(cfxy[0][1]), self.matplotlib.flip_y(cfxy[1][1]))
            min(cfxy[0][1], cfxy[1][1])
        )
        extents = abs(cfxy[0][1] - cfxy[1][1]), abs(cfxy[0][0] - cfxy[1][0])
        LOG.info(f'filtering for {expr=} {params=} {anchor=} {extents=}')

        colors = COLOR_MAP['BLACK'], COLOR_MAP['GREY']
        rect = self.matplotlib.create_rectangle(anchor, extents, colors)
        rect.set(hatch=hatch_pattern[which])
        self.matplotlib.axes.add_patch(rect)
        return topic

    def _init_content_filter_color(self, topic, which, cfcolor):
        expr = "color MATCH %0"
        params = [f"'{cfcolor}'"]  # doubly-quoted string is needed, i.e. ["'RED'"]
        LOG.debug(f'filtering for {expr=} {params=}')
        return dds.ContentFilteredTopic(topic, f"CFTcolor-{which}", dds.Filter(expr, params))

    def get_max_samples_per_instance(self, which):
        """ helper to fetch depth from a reader"""
        return self.reader_dic[which].qos.resource_limits.max_samples_per_instance

    def process_state(self, reader, info):
        """react to a status change"""
        if reader.status_changes & dds.StatusMask.LIVELINESS_LOST is not None:
            LOG.warning('LIVELINESS LOST')
            ihandle = info.instance_handle
            print(f'{str(ihandle)=} {reader.status_changes=} {dir(reader)=}')
            ##print(f'{reader.key_value(ihandle)=} {reader.is_matched_publication_alive=}')
            self.do_mark_gone(reader)
        if reader.status_changes & dds.StatusMask.LIVELINESS_CHANGED is not None:
            LOG.warning(f'LIVELINESS CHANGED {reader.liveliness_changed_status.alive_count_change}')
            self.do_mark_back(reader)
        if reader.status_changes & dds.StatusMask.SAMPLE_LOST is not None:
            LOG.warning('SAMPLE_LOST')

    def handle_one_sample(self, which, seq, data, handle):
        """update the poly_dic with fresh shape info"""
        ## create/update a matplotlib polygon from the sample data, add to poly_dic
        ## remove the prior poly's edge
        self.sample_counter.update([f'{which}r'])
        #LOG.warning(self.sample_counter[f'{which}r'])
        instance_gen_key = f"{which}-{data.color}"
        #LOG.info('sample:%s', data)
        inst = self.instance_gen_dic.get(instance_gen_key)
        if inst:  # same key for shape
            shape = self.shape_dic[instance_gen_key]
            #LOG.info('update:%s', data)
            shape.update(data.x, data.y, data.angle if self.args.extended else None)
            ##if self.sample_counter[f'{which}r'] > 100:
                ##pass #shape.mark_unknown(self.plt)
        else:
            LOG.info(f'{which=} {handle=}')
            inst = InstanceGen(self.get_max_samples_per_instance(which))
            self.instance_gen_dic[instance_gen_key] = inst
            LOG.info(f'ADD {instance_gen_key=} at {handle=}')
            self.handles_set.add(handle)
            self.poly_pub_dic[handle].append(instance_gen_key)
            LOG.info(f'{self.poly_pub_dic[handle]=}')
            shape = Shape.from_sub_sample(
                matplotlib=self.matplotlib,
                which=which,
                seq=seq,
                data=data,
                extended=self.args.extended
            )
        self.shape_dic[instance_gen_key] = shape
        inst_ix = inst.next()
        LOG.debug('SHAPE: shape:%s, inst_ix=%d', shape, inst_ix)
        poly_key = self.form_poly_key(which, shape.color, inst_ix)
        poly = self.poly_dic.get(poly_key)
        if self.args.justdds:
            LOG.info("early exit")
            return
        if not poly:
            poly = shape.create_poly()
            self.poly_dic[poly_key] = poly
            LOG.debug('added poly_key:%s', poly_key)
            self.matplotlib.axes.add_patch(poly)

        points = shape.get_points()
        shape.set_poly_center(poly, which, points)
        poly.set(lw=self.WIDE_EDGE_LINE_WIDTH, zorder=shape.zorder)

        prev_poly_key = self.form_poly_key(which, shape.color, inst.get_prev_ix())
        if prev_poly_key == poly_key:
            return  # history depth of 1, so nothing else to do
        prev_poly = self.poly_dic.get(prev_poly_key)
        if prev_poly:
            prev_poly.set(lw=self.THIN_EDGE_LINE_WIDTH)

    def _mark_gone(self, gone_keys):
        LOG.info(f'{gone_keys=}')
        LOG.info(f'{self.poly_pub_dic=}')
        LOG.info(f'{self.shape_dic=}')
        LOG.info(f'{self.poly_dic=}')
        new_gones = {}
        for poly_key in self.poly_dic.keys():
            LOG.info(f'checking {poly_key=}')
            if self.is_poly_key_gone(poly_key):
                continue
            for gone_key in gone_keys:
                if gone_key in poly_key:
                    shape = self.shape_dic[gone_key]
                    key, gone = self.mark_gone(shape, poly_key)
                    new_gones[key] = gone
        for key, value in new_gones.items():
            self.poly_dic[key] = value

    def do_mark_gone(self, p_reader):
        """update status and mark shape gone"""
        handles = p_reader.matched_publications
        LOG.info(f'{handles=} {str(handles)=}')
        handles_set = {str(handle) for handle in handles}
        missing_handle_set = self.handles_set - handles_set
        LOG.info(f'{missing_handle_set=} {handles_set=} {self.handles_set=}')
        if len(missing_handle_set):
            for missing_handle in missing_handle_set:
                self._mark_gone(self.poly_pub_dic[missing_handle])
                LOG.info('missing in set')
        for handle in handles:
            if not p_reader.is_matched_publication_alive(handle):
                self._mark_gone(self.poly_pub_dic[handle])
                LOG.info('missing in handle')
            else:
                LOG.info(f'ALIVE {handle=}')
        self.handles_set -= missing_handle_set

    def do_mark_back(self, p_reader):
        LOG.info('TBD')
        # TODO - mark this as back to life

    def handle_samples(self, reader, which):
        """get samples and handle each"""

        LOG.debug('START cntr: %d', self.sample_counter)
        for data, info in reader.take():
            if info.valid:
                LOG.info('sample:%s', data)
                self.handle_one_sample(
                    which,
                    info.reception_sequence_number.value,
                    data,
                    str(info.publication_handle)
                )
            else:
                LOG.info(f"State changed: {info.state}")
                self.process_state(reader, info)

    def draw(self, _):
        """The animation function, called periodically in a set interval, reads the
        last image received and draws it"""
        for which, reader in self.reader_dic.items():
            self.handle_samples(reader, which)
            self.sleep_as_needed()

        return self.poly_dic.values()  # give back the updated values so they are rendered
