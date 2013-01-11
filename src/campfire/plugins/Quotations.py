#!/usr/bin/env python
# -*- coding: utf-8 -*-
##
# python stdlib
import random

##
# campfire.api
from campfire.utils import Plugin
from event import synchronous


class Quotations(Plugin):
    """
    Quotations plugin.

    Handles empty messages posted by users
    """

    def __init__(self, quotations):
        """
        Plugin object initialization
        """
        self.quotations = quotations
        self._selected_quotations = []
        self.preselect_size = 30

    def _mapping(self):
        """
        Returns information about event listeners mapping
        """
        return [('message.received', self.on_new_message, 100)] # AFTER Voices!

    @synchronous
    def on_new_message(self, event, data):
        """
        Handles new message
        """
        if data is None:
            return data
        # single space
        if ' ' == data['text']:
            data['text'] = 'Cyt...'
        # double space
        elif '  ' == data['text']:
            data['text'] = 'Cytcyt.'
        # message consisted of blank chars only
        elif 0 == len(data['text'].strip()):
            try:
                # preselect quotations
                if len(self._selected_quotations) == 0:
                        self._selected_quotations = random.sample(\
                            self.quotations, self.preselect_size)
                data['me'] = True
                data['text'] = self._selected_quotations.pop()
            except ValueError:
                data['text'] = 'Cytcytcyt.'
        return data
