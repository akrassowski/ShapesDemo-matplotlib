#!/usr/bin/env python

###############################################################################
# (c) Copyright, Real-Time Innovations, 2021. All rights reserved.            #
# No duplications, whole or partial, manual or electronic, may be made        #
# without express written permission.  Any such copies, or revisions thereof, #
# must display this notice unaltered.                                         #
# This code contains trade secrets of Real-Time Innovations, Inc.             #
###############################################################################

"""Reads Shapes and displays them"""


# python imports
import logging
import os
import sys
import time

# Connext imports
import rti.connextdds as dds

from Connext import Connext
from Shape import Shape
from InstanceGen import InstanceGen

LOG = logging.getLogger(__name__)


class ConnextPub(Connext):

    def __init__(self, args):
        super().__init__(args)

    def start(self, fig, axes):
        """First, some globals and helpers"""
        self.fig = fig
        self.axes = axes


