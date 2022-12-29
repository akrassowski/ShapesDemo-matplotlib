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

# Connext imports
import rti.connextdds as dds

LOG = logging.getLogger(__name__)


class ShapeListener(dds.NoOpDataReaderListener):
    """Use Listener for out-of-band notification of Liveliness change"""
    _status_mask = (
        dds.StatusMask.REQUESTED_DEADLINE_MISSED |
        dds.StatusMask.SAMPLE_REJECTED |
        dds.StatusMask.SAMPLE_LOST |
        dds.StatusMask.REQUESTED_INCOMPATIBLE_QOS |
        dds.StatusMask.SUBSCRIPTION_MATCHED |
        dds.StatusMask.LIVELINESS_LOST |
        dds.StatusMask.LIVELINESS_CHANGED
    )

    listener_called = False  # TODO test me

    # pylint: disable=line-too-long, unused-argument
    def on_requested_deadline_missed(self, reader: dds.DataReader, status: dds.RequestedDeadlineMissedStatus):
        LOG.warning("Deadline missed")

    def on_sample_rejected(self, reader: dds.DataReader, status: dds.SampleRejectedStatus):
        LOG.warning("Sample rejected")

    def on_sample_lost(self, reader: dds.DataReader, status: dds.SampleLostStatus):
        LOG.warning("Sample lost")

    def on_requested_incompatible_qos(self, reader: dds.DataReader, status: dds.RequestedIncompatibleQosStatus):
        LOG.warning("Requested incompatible QoS")

    def on_subscription_matched(self, reader: dds.DataReader, status: dds.SubscriptionMatchedStatus):
        LOG.warning("Subscription matched")

    def on_liveliness_changed(self, reader: dds.DataReader, status: dds.LivelinessChangedStatus):
        LOG.warning("Liveliness changed")


    def get_mask(self):
        """return the mask for all the handlers"""
        return self._status_mask
