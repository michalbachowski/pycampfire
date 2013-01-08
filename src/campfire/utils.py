#!/usr/bin/env python
# -*- coding: utf-8 -*-
from event import Listener, synchronous


class Plugin(Listener):
    """
    Base abstract Plugin class
    """

    @synchronous
    def init(self, event):
        """
        Method called on chat initialization
        """
        return self._init(event)

    def _init(self, event):
        """
        Method called on chat initialization (this should be implemented)
        """
        pass

    @synchronous
    def shutdown(self, event):
        """
        Method called on chat shutdown
        """
        return self._shutdown(event)

    def _shutdown(self, event):
        """
        Method called on chat shutdown (this should be implemented)
        """
        pass

    def mapping(self):
        """
        Returns list of listeners to be attached to dispatcher.
        [(event name, listener, priority), (event name, listener, priority)]
        """
        return [('chat.init', self.init), ('chat.shutdown', self.shutdown)] + \
            self._mapping()

    def _mapping(self):
        """
        Returns list of listeners to be attached to dispatcher.
        [(event name, listener, priority), (event name, listener, priority)]
        """
        raise NotImplementedError('Return list of tuples with ' +\
            '(event, callback priority) mappings')
