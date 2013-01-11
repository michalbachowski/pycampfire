#!/usr/bin/env python
# -*- coding: utf-8 -*-

#!/usr/bin/env python
# -*- coding: utf-8 -*-

##
# campfire.api
from campfire.utils import Plugin
from event import synchronous

class Typing(Plugin):
    """
    Typing plugin.

    Handles "/typing" messages
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
        data['typing'] = '/typing' == data['text']
        return data
