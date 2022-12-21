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
import time

# Connext imports
import rti.connextdds as dds

from Connext import Connext
from InstanceGen import InstanceGen
from Shape import Shape
from ShapeListener import ShapeListener

LOG = logging.getLogger(__name__)


class ConnextSubscriber(Connext):
    """Subscriber can subscribe to one or more shapes"""

    def __init__(self, args, config):
        super().__init__(args)
        self.instance_gen_dic = {}  # Topic-color: InstanceGen
        self.shape_dic = {}  # Topic-color: InstanceGen
        self.reader_dic = {}  # one reader per Shape key: CST values: dds.DataReader
        self.poly_pub_dic = defaultdict(list)  # key: pubHandle values: [poly_key1, poly_key2...]
        self.handles_set = set()
        self.subscriber = dds.Subscriber(self.participant_with_qos)
        reader_qos = self.qos_provider.datareader_qos
        LOG.info('config=%s', config)
        #topic = dds.Topic(self.participant, 'Square', ShapeTypeExtended)

        listener = ShapeListener()
        status_mask = listener.get_mask()
        for which in 'S':  #config.keys():
            LOG.info(f'Subscribing to {which=} {config[which]=}')
            if 1==2:  # TODO fix me
                self.reader_dic[which] = dds.DynamicData.DataReader(
                    self.subscriber, self.topic_dic[which], reader_qos)
            else:
                self.reader_dic[which] = dds.DataReader(
                    self.subscriber,
                    self.stopic_dic[which],
                    reader_qos,
                    listener,
                    status_mask
                )

    def get_max_samples_per_instance(self, which):
        """ helper to fetch depth from a reader"""
        return self.reader_dic[which].qos.resource_limits.max_samples_per_instance

    def start(self, fig, axes):
        """First, some globals and helpers"""
        super().start(fig, axes)

    def process_state(self, reader):
        """react to a status change"""
        if reader.status_changes & dds.StatusMask.LIVELINESS_LOST is not None:
            LOG.warning('LIVELINESS LOST')
            self.do_mark_gone(reader)
        if reader.status_changes & dds.StatusMask.LIVELINESS_CHANGED is not None:
            LOG.warning(f'LIVELINESS CHANGED {reader.liveliness_changed_status.alive_count_change}')
        if reader.status_changes & dds.StatusMask.LIVELINESS_CHANGED is not None:
            LOG.warning('LIVELINESS CHANGED')
        if reader.status_changes & dds.StatusMask.SAMPLE_LOST is not None:
            LOG.warning('SAMPLE_LOST')

    def handle_one_sample_old(self, which, sample):
        """update the poly_dic with fresh shape info"""
        ## create/update a matplotlib polygon from the sample data, add to poly_dic
        ## remove the prior poly's edge
        self.sample_counter.update([f'{which}r'])
        LOG.warning(self.sample_counter[f'{which}r'])
        #instance_gen_key = f'{which}-{shape.color}'
        instance_gen_key = self.form_poly_key(which, sample.data['color'])
        #LOG.info('sample:%s', sample.data.to_string())
        inst = self.instance_gen_dic.get(instance_gen_key)
        if inst:  # same key for shape
            shape = self.shape_dic[instance_gen_key]
            if self.args.extended:
                shape.update_extended(sample.data['x'], sample.data['y'], sample.data['angle'])
            else:
                shape.update(sample.data['x'], sample.data['y'])
            if self.sample_counter[f'{which}r'] > 100:
                pass #shape.mark_unknown(self.plt)
        else:
            inst = InstanceGen(self.get_max_samples_per_instance(which))
            self.instance_gen_dic[instance_gen_key] = inst
            shape = Shape.from_sub_sample_seq(
                seq=sample.info.reception_sequence_number.value,
                which=which,
                limit_xy=self.args.graph_xy,
                data=sample.data,
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
            self.axes.add_patch(poly)

        points = shape.get_points()
        Shape.set_poly_center(poly, which, points)
        poly.set(lw=self.WIDE_EDGE_LINE_WIDTH, zorder=shape.zorder)

        prev_poly_key = self.form_poly_key(which, shape.color, inst.get_prev_ix())
        prev_poly = self.poly_dic.get(prev_poly_key)
        if prev_poly:
            prev_poly.set(lw=self.THIN_EDGE_LINE_WIDTH)

    def handle_one_sample(self, which, seq, data, handle):
        """update the poly_dic with fresh shape info"""
        ## create/update a matplotlib polygon from the sample data, add to poly_dic
        ## remove the prior poly's edge
        self.sample_counter.update([f'{which}r'])
        #LOG.warning(self.sample_counter[f'{which}r'])
        instance_gen_key = f"{which}-{data.color}"
        #LOG.info('sample:%s', data.to_string())
        inst = self.instance_gen_dic.get(instance_gen_key)
        if inst:  # same key for shape
            shape = self.shape_dic[instance_gen_key]
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
            shape = Shape.from_sub_sample_seq(
                which=which,
                limit_xy=self.args.graph_xy,
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
            self.axes.add_patch(poly)

        points = shape.get_points()
        Shape.set_poly_center(poly, which, points)
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
                    _, color, _ = self.crack_poly_key(poly_key)
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
        for handle in handles:
            if not p_reader.is_matched_publication_alive(handle):
                self._mark_gone(self.poly_pub_dic[handle])
            else:
                LOG.info(f'ALIVE {handle=}')
        self.handles_set -= missing_handle_set

    @staticmethod
    def print_guids(info):
        def guid2str(guid):
            return '.'.join([ str(guid[x]) for x in range(16)])

        print(f'{guid2str(info.original_publication_virtual_guid)=}')
        print(f'{guid2str(info.related_original_publication_virtual_guid)=}')
        print(f'{guid2str(info.related_source_guid)=}')
        print(f'{guid2str(info.source_guid)=}')
        #print(f'{info.publication_handle=}')

    def handle_samples(self, reader, which):
        """get samples and handle each"""

        LOG.debug('START cntr: %d', self.sample_counter)
        for data, info in reader.take():
            if info.valid:
                #self.print_guids(info)
                self.handle_one_sample(
                    which,
                    info.reception_sequence_number.value,
                    data,
                    str(info.publication_handle)
                )
            else:
                LOG.info(f"State changed: {info.state}")
                self.process_state(reader)


        if self.args.nap:
            time.sleep(self.args.nap)
            LOG.info(f'Sleeping {self.args.nap=}')

        LOG.debug('cntr:%d', self.sample_counter)


    def draw(self, _):
        """The animation function, called periodically in a set interval, reads the
        last image received and draws it"""
        readers = self.reader_dic.values()
        whiches = self.reader_dic.keys()
        for reader, which in zip(readers, whiches):
            self.handle_samples(reader, which)

        return self.poly_dic.values()  # give back the updated values so they are rendered
