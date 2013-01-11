#!/usr/bin/env python
# -*- coding: utf-8 -*-

##
# python stdlib
import cgi

##
# campfire.api
from campfire.utils import Plugin
from event import synchronous

class Tidy(Plugin):
    """
    Tidy plugin.

    Escapes HTML from message text
    """

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
        data['text'] = cgi.escape(data['text'], True)
        return data
