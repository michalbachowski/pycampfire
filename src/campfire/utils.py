#!/usr/bin/env python
# -*- coding: utf-8 -*-
from event import Listener, synchronous


class Plugin(Listener):
    """
    Base abstract Plugin class
    """
    user_attrs = ['id', 'ip', 'name']

    def __init__(self):
        """
        Object inizialization
        """
        self.log = None

    def match_user(self, user, possibilities):
        """
        Tests whether something within given user structure is contained in 
        given possibilities
        """
        return [v for (k, v) in user.iteritems() \
            if k in Plugin.user_attrs and v in possibilities]


    @synchronous
    def init(self, event):
        """
        Method called on chat initialization
        """
        self.log = event['log']
        self.log.debug('msg=initializing plugin; plugin=%s', \
            self.__class__.__name__)
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
        self.log.debug('msg=shutting down plugin; plugin=%s', \
            self.__class__.__name__)
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
        return []
