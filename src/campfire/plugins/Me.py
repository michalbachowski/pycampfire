#!/usr/bin/env python
# -*- coding: utf-8 -*-

##
# campfire.api
from campfire.utils import Plugin


class Me(Plugin):
    """
    Me plugin.

    Handles "/me" messages
    """

    def _mapping(self):
        """
        Returns information about event listeners mapping
        """
        return [('message.received', self.on_new_message)]
    
    def on_new_message(self, event, data):
        """
        Handles new message
        """
        if data is None:
            return data
        data['me'] = '/me ' == data['text'][:4]
        if data['me']:
            data['text'] = data['text'][4:]
        return data
