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

    def _init(self, event):
        """
        Plugin initialization
        """
        self.voices = {}

    def _mapping(self):
        """
        Returns information about event listeners mapping
        """
        return [('voices.voice.add', self.add_voice), \
            ('message.received', self.on_new_message, 70)] # BEFORE Quotations!

    @synchronous
    def add_voice(self, event):
        """
        Adds new voice
        """
        self.voices[event['name']] = event['voice']
        return True
    
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
