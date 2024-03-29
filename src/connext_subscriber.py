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
import json
import logging

# Connext imports
import rti.connextdds as dds

from connext import Connext, possibly_log_qos
from instance_gen import InstanceGen
from shape import Shape, COLOR_MAP
from shape_listener import ShapeListener

LOG = logging.getLogger(__name__)

class ConnextSubscriber(Connext):
    """Subscriber can subscribe to one or more shapes"""

    def __init__(self, matplotlib, args, config):
        super().__init__(matplotlib, args)
        self.instance_gen_dic = {}  # Topic-color: InstanceGen
        self.shape_dic = {}  # Topic-color: InstanceGen
        self.reader_dic = {}  # one reader per Shape key: CST values: dds.DataReader
        self.poly_pub_dic = defaultdict(list)  # key: pubHandle values: [poly_key1, poly_key2...]
        self.subscriber = dds.Subscriber(self.participant_with_qos)
        possibly_log_qos(self.args.log_qos, self.subscriber)
        reader_qos = self.qos_provider.datareader_qos

        listener = ShapeListener(args)
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
            possibly_log_qos(self.args.log_qos, self.reader_dic[which])

    def _init_get_topic(self, which, config):
        """get a Content Filtered or normal Topic"""
        topic = self.topic_dic[which]
        in_ex = ('in' if config[which].get('content_filter_include', True) else 'ex') + 'clusive'
        cfxy = config[which].get('content_filter_xy')
        if cfxy:
            topic = self._init_content_filter_xy(topic, which, cfxy, in_ex)
        else:
            cf_color = config[which].get('content_filter_color')
            if cf_color:
                topic = self._init_content_filter_color(topic, which, cf_color, in_ex)
        return topic

    def _init_content_filter_xy(self, topic, which, cfxy, in_ex):
        """handle filter region with top-left and bottom-right specified"""
        hatch_pattern = { 'C': 'o', 'T': '/', 'S': '+' }
        if in_ex[0:2] == 'in':
            expr = "x > %0 AND y > %1 AND x < %2 and y < %3"
        else:
            expr = "x <= %0 AND y <= %1 AND x >= %2 and y >= %3"
        params = [str(n) for sublist in cfxy for n in sublist]
        topic = dds.ContentFilteredTopic(topic, f"CFTxy-{which}-{in_ex}", dds.Filter(expr, params))
        anchor = (
            min(cfxy[0][0], cfxy[1][0]),
            #min(self.matplotlib.flip_y(cfxy[0][1]), self.matplotlib.flip_y(cfxy[1][1]))
            min(cfxy[0][1], cfxy[1][1])
        )
        extents = abs(cfxy[0][1] - cfxy[1][1]), abs(cfxy[0][0] - cfxy[1][0])
        LOG.info(f'filtering for {expr=} {params=} {anchor=} {extents=} {in_ex=}')

        colors = COLOR_MAP['BLACK'], COLOR_MAP['GREY']
        rect = self.matplotlib.create_rectangle(anchor, extents, colors)
        rect.set(hatch=hatch_pattern[which])
        self.matplotlib.axes.add_patch(rect)
        return topic

    def _init_content_filter_color(self, topic, which, cf_color, in_ex):
        expr = "color MATCH %0"
        if in_ex[0:2] != 'in':
            expr = "NOT " + expr
        params = [f"'{cf_color}'"]  # doubly-quoted string is needed, i.e. ["'RED'"]
        LOG.info(f'filtering for {expr=} {params=} {in_ex=}')
        return dds.ContentFilteredTopic(topic, f"CFT-{which}-{in_ex}", dds.Filter(expr, params))

    def get_max_samples_per_instance(self, which):
        """ helper to fetch depth from a reader"""
        return self.reader_dic[which].qos.resource_limits.max_samples_per_instance

    @staticmethod
    def pprint_dict(a_dic):
        """helper to pretty-print a dictionary"""
        print(str(json.dumps(a_dic, indent=4, separators=(',', ': '))))

    def process_state(self, reader, info):
        """react to a status change"""
        if reader.status_changes & dds.StatusMask.LIVELINESS_LOST is not None:
            LOG.warning(f'LIVELINESS LOST for: {reader.topic_name}')
            ihandle = info.instance_handle
            ##self.pprint_dict(dir(reader))
            ##self.pprint_dict(dir(info))
            LOG.info(f'{str(ihandle)=} {info.publication_handle=} {info.source_guid}')
            try:
                #LOG.info(f'{reader.is_matched_publication_alive(ihandle)=}')
                LOG.info(f'{reader.status_changes=}')
            except Exception as exc:
                LOG.info(f'TOO GENERAL: {exc=}')
            self.mark_reader_gone(reader, str(info.source_guid))
        if reader.status_changes & dds.StatusMask.LIVELINESS_CHANGED is not None:
            LOG.warning(f'LIVELINESS CHANGED {reader.liveliness_changed_status.alive_count_change}')
            LOG.warning(f'LIVELINESS CHANGED {reader.matched_publications=} ')
            ##if reader.liveliness_changed_status.alive_count_change:
                ##self.do_mark_back(reader)
        if reader.status_changes & dds.StatusMask.SAMPLE_LOST is not None:
            LOG.warning('SAMPLE_LOST')

    def handle_one_sample(self, which, seq, data, pub_handle):
        """update the poly_dic with fresh shape info"""

        def _create_shape(self, which, instance_gen_key):
            """helper to create a new shape"""
            LOG.info(f'{which=} {pub_handle=}')
            inst = InstanceGen(self.get_max_samples_per_instance(which))
            self.instance_gen_dic[instance_gen_key] = inst
            LOG.info(f'ADD {instance_gen_key=} at {pub_handle=}')
            self.poly_pub_dic[pub_handle].append(instance_gen_key)
            LOG.info(f'{self.poly_pub_dic[pub_handle]=}')
            return inst, Shape.from_sub_sample(
                matplotlib=self.matplotlib,
                which=which,
                seq=seq,
                data=data,
                extended=self.args.extended
            )

        def _fixup_edges(self, which, color, prev_ix, poly_key):
            """helper to change 2nd instance's edge"""
            prev_poly_key = self.form_poly_key(which, color, prev_ix)
            if prev_poly_key == poly_key:
                return  # history depth of 1, so nothing else to do
            prev_poly = self.poly_dic.get(prev_poly_key)
            if prev_poly:
                prev_poly.set(lw=self.matplotlib.THIN_EDGE_LINE_WIDTH)

        ## create/update a matplotlib polygon from the sample data, add to poly_dic
        ## remove the prior poly's edge
        self.sample_counter.update([f'{which}-read'])
        instance_gen_key = self.form_poly_key(which, data.color)
        #LOG.info('sample:%s', data)
        inst = self.instance_gen_dic.get(instance_gen_key)
        if inst:  # same key for shape
            shape = self.shape_dic[instance_gen_key]
            if shape.gone:
                # on update of a sample for a Gone instance, remove all the Xs
                # Alternatively, recode to remove instances one-at-a-time like ShapesDemoJ does
                gone_keys = [key for key in self.poly_dic if instance_gen_key in key]
                for key in gone_keys:
                    del self.poly_dic[key]
                LOG.info(f'{gone_keys=}')
            shape.update(data.x, data.y, data.angle if self.args.extended else None)
        else:
            inst, shape = _create_shape(self, which, instance_gen_key)
        self.shape_dic[instance_gen_key] = shape  # add new or updated shape to dict
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

        shape.set_poly_center(poly, which, shape.get_points())
        poly.set(lw=self.matplotlib.WIDE_EDGE_LINE_WIDTH, zorder=shape.zorder)
        _fixup_edges(self, which, shape.color, inst.get_prev_ix(), poly_key)

    def _mark_gone(self, gone_guid):
        """add a gone multistep line Xing the shape"""
        new_gones = {}
        gone_keys = self.poly_pub_dic.get(gone_guid)
        if gone_keys is None:
            LOG.warning(f'{gone_guid=} {self.poly_pub_dic=}')
        for poly_key, poly in self.poly_dic.items():
            LOG.debug('checking %s', poly_key)
            for gone_key in gone_keys or []:
                LOG.info(f'checking {gone_key=}')
                if gone_key in poly_key:
                    LOG.info(f'match: {gone_key=} {self.shape_dic=} {poly_key=}')
                    shape = self.shape_dic[gone_key]
                    key, gone = self.mark_gone(shape, poly_key)
                    new_gones[key] = gone
                else:
                    LOG.info(f'no match, add to new dic {gone_key=} {poly_key=} {poly=}')
        # add new gone markers to the displayable polygons dic so plotlib will show them
        LOG.info(f'{new_gones=}')
        for key, value in new_gones.items():
            self.poly_dic[key] = value
        LOG.debug('poly_dic: %s', self.poly_dic)

    def mark_reader_gone(self, p_reader, guid):
        """update status and mark shape gone"""
        handles = p_reader.matched_publications
        LOG.info(f'{handles=} {str(handles)=}, {guid=}')
        self._mark_gone(guid)

    def handle_samples(self, reader, which):
        """get samples and handle each"""
        for data, info in reader.take():
            if info.valid:
                LOG.debug('sample:%s', data)
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
        return self.poly_dic.values()  # give back the updated values so they are rendered
