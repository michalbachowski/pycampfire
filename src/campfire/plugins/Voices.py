#!/usr/bin/env python
# -*- coding: utf-8 -*-

##
# campfire.api
from campfire.utils import Plugin
from event import synchronous


class Voices(Plugin):
    """
    Voices plugin.

    Handles empty messages posted by some puppets and changes them
    """

    def __init__(self, voices):
        """
        Plugin initialization
        """
        self.voices = voices

    def _mapping(self):
        """
        Returns information about event listeners mapping
        """
        # BEFORE Quotations plugin!
        return [('message.received', self.on_new_message, 70)]
   
    @synchronous
    def on_new_message(self, event, data):
        """
        Handles new message
        """
        if data is None:
            return data
        if 'as_puppet' not in data:
            return data
        if not data['as_puppet']:
            return data
        if data['text'] != ' ':
            return data
        if data['from']['name'] not in self.voices:
            return data
        data['text'] = self.voices[data['from']['name']]
        return data
