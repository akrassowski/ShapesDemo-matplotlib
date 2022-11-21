#!/usr/bin/env python

###############################################################################
# (c) Copyright, Real-Time Innovations, 2021. All rights reserved.            #
# No duplications, whole or partial, manual or electronic, may be made        #
# without express written permission.  Any such copies, or revisions thereof, #
# must display this notice unaltered.                                         #
# This code contains trade secrets of Real-Time Innovations, Inc.             #
###############################################################################

"""Instance Generator """
# Subscribed instances are differentiated by an instance id, manage the range

# python imports
#import logging

# LOG = logging.getLogger(__name__)


class InstanceGen:
    """returns instance index confined to the range"""

    def __init__(self, _range):
        self._range = _range
        self.current_ix = 0
        self.instance = 0

    def get_prev_ix(self):
        """@return the previous given number with no changes"""
        return (self.current_ix - 1 + self._range) % self._range

    def next(self):
        """@return the next instance index and move along"""
        self.current_ix = self.instance
        self.instance = (self.instance + 1) % self._range
        return self.current_ix
