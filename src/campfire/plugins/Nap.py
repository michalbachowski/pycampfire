#!/usr/bin/env python
# -*- coding: utf-8 -*-
##
# python stdlib
import random

##
# campfire.api
from campfire.utils import Plugin
from event import synchronous

class Nap(Plugin):
    """
    Nap plugin.

    Handles "/nap" messages
    """

    def __init__(self, quotes):
        """
        Plugin initialization
        """
        self.quotes = list(quotes)

    def _mapping(self):
        """
        Returns information about event listeners mapping
        """
        return [('message.received', self.on_new_message)]

    @synchronous
    def on_new_message(self, event, data):
        """
        Handles new message
        """
        if data is None:
            return data
        if '/nap' == data['text']:
            data['me'] = True
            data['nap'] = True
            try:
                data['text'] = random.choice(self.quotes) + "..."
            except IndexError:
                pass
        return data
