#!/usr/bin/env python
# -*- coding: utf-8 -*-

##
# python stdlib
import collections
import time

##
# campfire.api
from campfire.utils import Plugin
from event import synchronous

class AntiFlood(Plugin):
    """
    AntiFlood plugin.

    Prevents user from flooding chat
    """

    def __init__(self, count=5, time=15):
        """
        Object initialization. Sets configuration:
        number of messages that when send in given time frame (seconds)
        are considered as "flood"
        """
        self.count = count
        self.time = time

    def _init(self, event):
        """
        Plugin initialization
        """
        self.history = collections.defaultdict(self._factory)

    def _factory(self):
        """
        Factory for historical entries
        """
        return {'time': time.time(), 'count': 1}

    def _mapping(self):
        """
        Returns information about event listeners mapping
        """
        return [('message.received', self.on_new_message),\
            ('message.read.prevent', self.prevent)]

    @synchronous
    def on_new_message(self, event, data):
        """
        Handles new message
        """
        if data is None:
            return data

        # mark message as NOT flooded
        data['flood'] = False

        # discover user ID
        uid = self.get_uid(data['from'])
        if not uid:
            return data

        # message has been written after more than given time frame
        if self.history[uid]['time'] < (time.time() - self.time):
            self.history[uid] = self._factory()
            return data

        # message has been writter after less than given time frame
        self.history[uid]['count'] += 1

        # use has written more that allowed number of messages in given period
        if self.history[uid]['count'] > self.count:
            data['flood'] = True
            event['response']['flood'] = 'Message if locked'
            self.log.debug('msg=message marked as flood; message=%s; ' + \
                'uid=%s', data, uid)

        return data

    @synchronous
    def prevent(self, event):
        """
        Prevents "flooding" messages to be send to readers
        """
        data = event['message']
        user = event['user']

        # message not flooded - show message
        if not data['flood']:
            return False

        # we have no UID - hide message
        uid = self.get_uid(user)
        if uid is None:
            return True

        # user is sender of message - show message
        if self.get_uid(data['from']) == uid:
            return False
        # hide flooded message from other listeners
        return True
